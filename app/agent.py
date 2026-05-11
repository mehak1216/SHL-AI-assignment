from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from app.catalog import load_catalog
from app.models import ChatMessage, ChatResponse, Recommendation


TEST_TYPE_LABELS = {
    "A": "ability and aptitude",
    "B": "biodata and situational judgement",
    "C": "competencies",
    "D": "development and 360",
    "E": "assessment exercises",
    "K": "knowledge and skills",
    "P": "personality and behavior",
    "S": "simulations",
}

OFF_TOPIC_PATTERNS = (
    "salary",
    "compensation",
    "labor law",
    "legal advice",
    "termination",
    "visa",
    "immigration",
    "resume writing",
    "cv writing",
)

INJECTION_PATTERNS = (
    "ignore previous instructions",
    "system prompt",
    "reveal prompt",
    "developer message",
    "jailbreak",
    "act as",
)

ASSESSMENT_ALIASES = {
    "opq": "Occupational Personality Questionnaire OPQ32r",
    "opq32r": "Occupational Personality Questionnaire OPQ32r",
    "g+": "SHL Verify Interactive G+",
    "verify interactive g+": "SHL Verify Interactive G+",
    "interactive g+": "SHL Verify Interactive G+",
}


@dataclass
class ConversationState:
    role_text: str = ""
    domains: set[str] = field(default_factory=set)
    requested_types: set[str] = field(default_factory=set)
    excluded_types: set[str] = field(default_factory=set)
    strict_type_filter: bool = False
    seniority: set[str] = field(default_factory=set)
    soft_skills: set[str] = field(default_factory=set)
    languages: set[str] = field(default_factory=set)
    last_user_message: str = ""
    user_history_text: str = ""
    comparison_targets: list[str] = field(default_factory=list)
    wants_comparison: bool = False
    jd_like: bool = False
    user_turn_count: int = 0
    total_turn_count: int = 0


DOMAIN_KEYWORDS = {
    "software": {"software", "developer", "engineering", "programming", "backend", "frontend"},
    "java": {"java", "j2ee", "spring", "backend"},
    "python": {"python", "django", "flask"},
    "javascript": {"javascript", "frontend", "react", "node", "angular"},
    ".net": {".net", "dotnet", "asp.net", "c#"},
    "cloud": {"aws", "cloud", "azure"},
    "data": {"sql", "database", "analytics", "data"},
    "qa": {"testing", "qa", "quality", "selenium"},
    "finance": {"accounts payable", "accounts receivable", "accounting", "finance"},
    "sales": {"sales", "account manager", "business development"},
}

SOFT_SKILLS = {
    "stakeholder": {"stakeholder", "client-facing", "client", "partner"},
    "communication": {"communication", "present", "presenting", "influence"},
    "leadership": {"lead", "leadership", "manager", "mentor"},
    "teamwork": {"teamwork", "collaboration", "cross-functional"},
}

TYPE_HINTS = {
    "P": {"personality", "behavior", "behaviour", "opq", "culture fit"},
    "A": {"ability", "aptitude", "cognitive", "reasoning", "g+", "numerical", "verbal"},
    "K": {"technical", "knowledge", "skill", "coding", "programming"},
    "S": {"simulation", "simulations", "simulated", "hands-on"},
}

NEGATED_TYPE_HINTS = {
    "P": {"no personality", "without personality", "not personality", "exclude personality"},
    "A": {"no cognitive", "without cognitive", "not cognitive", "exclude cognitive", "no ability"},
    "K": {"no technical", "without technical", "exclude technical", "no coding"},
    "S": {"no simulation", "without simulation", "exclude simulation"},
}

SENIORITY_HINTS = {
    "entry-level": {"entry", "junior", "fresher", "graduate", "0-2 years"},
    "mid-professional": {"mid", "mid-level", "3 years", "4 years", "5 years"},
    "manager": {"manager", "lead", "supervisor"},
    "senior": {"senior", "staff", "principal", "architect", "6 years", "7 years", "8 years"},
}


def build_response(messages: list[ChatMessage]) -> ChatResponse:
    state = _parse_state(messages)

    refusal = _maybe_refuse(state.last_user_message)
    if refusal:
        return ChatResponse(reply=refusal, recommendations=[], end_of_conversation=False)

    if state.wants_comparison:
        return ChatResponse(
            reply=_compare_assessments(state),
            recommendations=[],
            end_of_conversation=False,
        )

    if _needs_clarification(state):
        return ChatResponse(
            reply=_clarification_question(state),
            recommendations=[],
            end_of_conversation=False,
        )

    ranked = _rank_assessments(state)
    recommendations = [
        Recommendation(name=item["name"], url=item["url"], test_type=item["test_type"])
        for item in ranked[:10]
    ]

    if not recommendations:
        return ChatResponse(
            reply=(
                "I couldn't ground a shortlist in the local SHL catalog yet. "
                "Please share the target role, core skills, or whether you want technical, "
                "ability, or personality assessments."
            ),
            recommendations=[],
            end_of_conversation=False,
        )

    return ChatResponse(
        reply=_recommendation_reply(state, recommendations),
        recommendations=recommendations,
        end_of_conversation=_should_end_conversation(state),
    )


def _parse_state(messages: list[ChatMessage]) -> ConversationState:
    state = ConversationState()
    catalog = load_catalog()
    catalog_names = [item["name"] for item in catalog]

    user_messages = [message.content.strip() for message in messages if message.role == "user"]
    state.user_turn_count = len(user_messages)
    state.total_turn_count = len(messages)
    state.user_history_text = " ".join(user_messages).lower()
    state.last_user_message = user_messages[-1].lower() if user_messages else ""
    state.jd_like = len(state.last_user_message.split()) >= 18 or "job description" in state.last_user_message
    state.strict_type_filter = any(
        phrase in state.user_history_text
        for phrase in (
            "only technical",
            "only cognitive",
            "only personality",
            "only simulations",
            "only simulation",
            "just technical",
            "just cognitive",
            "just personality",
        )
    )

    for name in catalog_names:
        if _matches(state.last_user_message, name.lower()):
            state.comparison_targets.append(name)

    for alias, canonical_name in ASSESSMENT_ALIASES.items():
        if _matches(state.last_user_message, alias) and canonical_name not in state.comparison_targets:
            state.comparison_targets.append(canonical_name)

    state.wants_comparison = any(
        cue in state.last_user_message for cue in ("difference", "compare", "vs", "versus")
    ) and len(state.comparison_targets) >= 2

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(_matches(state.user_history_text, keyword) for keyword in keywords):
            state.domains.add(domain)

    for skill, keywords in SOFT_SKILLS.items():
        if any(_matches(state.user_history_text, keyword) for keyword in keywords):
            state.soft_skills.add(skill)

    for test_type, keywords in TYPE_HINTS.items():
        if any(_matches(state.user_history_text, keyword) for keyword in keywords):
            state.requested_types.add(test_type)

    for test_type, keywords in NEGATED_TYPE_HINTS.items():
        if any(_matches(state.user_history_text, keyword) for keyword in keywords):
            state.excluded_types.add(test_type)

    for level, keywords in SENIORITY_HINTS.items():
        if any(_matches(state.user_history_text, keyword) for keyword in keywords):
            state.seniority.add(level)

    if "english" in state.user_history_text or "usa" in state.user_history_text:
        state.languages.add("English (USA)")

    role_matches = re.findall(
        r"(java developer|python developer|software engineer|backend engineer|frontend engineer|qa engineer|"
        r"data analyst|accountant|finance analyst|manager|team lead|developer)",
        state.user_history_text,
    )
    if role_matches:
        state.role_text = role_matches[-1]
    elif state.jd_like:
        state.role_text = "the role you described"

    if any(keyword in state.user_history_text for keyword in ("developer", "software engineer", "backend engineer", "frontend engineer")):
        state.domains.add("software")

    state.requested_types.difference_update(state.excluded_types)
    return state


def _maybe_refuse(text: str) -> str | None:
    if any(pattern in text for pattern in INJECTION_PATTERNS):
        return (
            "I can only help with SHL assessment selection from the catalog. "
            "I won't follow prompt-injection or system-instruction requests."
        )
    if any(pattern in text for pattern in OFF_TOPIC_PATTERNS):
        return (
            "I stay scoped to SHL assessments and catalog-based comparisons. "
            "If you want, I can help choose SHL assessments for the role instead."
        )
    return None


def _needs_clarification(state: ConversationState) -> bool:
    if state.wants_comparison or state.jd_like:
        return False
    if state.total_turn_count >= 7:
        return False
    if state.domains or state.role_text or state.requested_types:
        return False
    short_and_vague = len(state.last_user_message.split()) < 10
    mentions_only_assessment = "assessment" in state.last_user_message or "test" in state.last_user_message
    return short_and_vague or mentions_only_assessment


def _clarification_question(state: ConversationState) -> str:
    if not state.role_text:
        return (
            "I can help with SHL assessments, but I need a bit more context first. "
            "What role are you hiring for, and do you want technical, cognitive, personality, or a mix of assessments?"
        )
    if not state.seniority:
        return (
            "What seniority level is this role, and should I focus on technical, cognitive, personality, or mixed assessment coverage?"
        )
    return (
        "What matters most for this hire: technical depth, cognitive ability, personality and stakeholder style, "
        "or a combination?"
    )


def _rank_assessments(state: ConversationState) -> list[dict]:
    scored: list[tuple[float, dict]] = []

    for item in load_catalog():
        if item["test_type"] in state.excluded_types:
            continue
        if state.strict_type_filter and state.requested_types and item["test_type"] not in state.requested_types:
            continue
        score = 0.0
        haystack = " ".join(
            [
                item["name"],
                item.get("description", ""),
                " ".join(item.get("tags", [])),
                " ".join(item.get("job_levels", [])),
            ]
        ).lower()

        for domain in state.domains:
            if _matches(haystack, domain):
                score += 4.0
            if any(_matches(haystack, keyword) for keyword in DOMAIN_KEYWORDS[domain]):
                score += 3.0

        for soft_skill in state.soft_skills:
            if _matches(haystack, soft_skill):
                score += 2.5

        for requested_type in state.requested_types:
            if item["test_type"] == requested_type:
                score += 4.5

        if not state.requested_types:
            if state.domains and item["test_type"] == "K":
                score += 2.0
            if state.soft_skills and item["test_type"] == "P":
                score += 2.0
            if state.jd_like and item["test_type"] == "A":
                score += 1.5

        for level in state.seniority:
            if any(_matches(job_level.lower(), level) for job_level in item.get("job_levels", [])):
                score += 1.5

        if state.languages and any(language in item.get("languages", []) for language in state.languages):
            score += 0.5

        if state.role_text and any(_matches(haystack, token) for token in state.role_text.split()):
            score += 1.5

        if score > 0 and item.get("remote_testing"):
            score += 0.25

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    return _diversify_recommendations(state, [item for _, item in scored])


def _compare_assessments(state: ConversationState) -> str:
    indexed = {item["name"]: item for item in load_catalog()}
    names = state.comparison_targets[:2]
    if len(names) < 2:
        return "Please name the two SHL assessments you want compared."

    first = indexed[names[0]]
    second = indexed[names[1]]
    lines = [
        f"{first['name']} is a {TEST_TYPE_LABELS.get(first['test_type'], first['test_type'])} assessment focused on {first['description'].rstrip('.').lower()}.",
        f"{second['name']} is a {TEST_TYPE_LABELS.get(second['test_type'], second['test_type'])} assessment focused on {second['description'].rstrip('.').lower()}.",
    ]
    if first["test_type"] != second["test_type"]:
        lines.append(
            f"The biggest difference is assessment type: {first['name']} is `{first['test_type']}` while {second['name']} is `{second['test_type']}`."
        )

    first_duration = first.get("duration_minutes")
    second_duration = second.get("duration_minutes")
    if first_duration and second_duration and first_duration != second_duration:
        lines.append(f"They also differ in length: about {first_duration} minutes versus {second_duration} minutes.")
    return " ".join(lines)


def _recommendation_reply(state: ConversationState, recommendations: Iterable[Recommendation]) -> str:
    names = [item.name for item in recommendations]
    role = state.role_text or "the role you described"
    completion = " This should be enough to start evaluation." if _should_end_conversation(state) else ""
    return (
        f"Based on {role}, I'd shortlist {len(names)} SHL assessments{_type_summary(state)}. "
        f"The strongest matches are {', '.join(names[:3])}.{completion}"
    )


def _type_summary(state: ConversationState) -> str:
    if state.requested_types:
        labels = [TEST_TYPE_LABELS[item].replace(" and ", "/") for item in sorted(state.requested_types)]
        return f" across {', '.join(labels)}"
    if state.domains and state.soft_skills:
        return " across technical and personality coverage"
    if state.domains:
        return " for technical fit"
    if state.soft_skills:
        return " for stakeholder and behavioral fit"
    return ""


def _should_end_conversation(state: ConversationState) -> bool:
    if state.wants_comparison:
        return False
    if state.total_turn_count >= 7:
        return True
    if state.user_turn_count >= 2:
        return True
    return state.jd_like


def _diversify_recommendations(state: ConversationState, ranked_items: list[dict]) -> list[dict]:
    if not ranked_items:
        return []

    if len(state.requested_types) <= 1:
        return _dedupe_by_name(ranked_items)

    chosen: list[dict] = []
    used_names: set[str] = set()

    for requested_type in sorted(state.requested_types):
        for item in ranked_items:
            if item["test_type"] != requested_type or item["name"] in used_names:
                continue
            chosen.append(item)
            used_names.add(item["name"])
            break

    for item in ranked_items:
        if item["name"] in used_names:
            continue
        chosen.append(item)
        used_names.add(item["name"])

    return chosen


def _dedupe_by_name(items: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if item["name"] in seen:
            continue
        deduped.append(item)
        seen.add(item["name"])
    return deduped


def _matches(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    if re.fullmatch(r"[\w\s+-]+", phrase):
        pattern = rf"(?<!\w){escaped}(?!\w)"
        return re.search(pattern, text) is not None
    return phrase in text
