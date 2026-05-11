from __future__ import annotations

import html

import streamlit as st

from app.agent import build_response
from app.catalog import load_catalog
from app.models import ChatMessage


SCENARIOS = {
    "Vague Query": "I need an assessment for a role I am hiring for.",
    "Technical + Stakeholder Fit": "Hiring a Java developer who works with stakeholders.",
    "Mid-Conversation Refinement": "Actually, add personality tests too.",
    "Grounded Comparison": "What is the difference between OPQ and G+?",
}

CATALOG = load_catalog()
CATALOG_BY_NAME = {item["name"]: item for item in CATALOG}


st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon=":briefcase:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None


def inject_styles() -> None:
    st.markdown(
        """
        <style>
          .stApp {
            background:
              radial-gradient(circle at top left, rgba(214, 140, 69, 0.20), transparent 24%),
              radial-gradient(circle at 80% 10%, rgba(13, 107, 93, 0.14), transparent 22%),
              linear-gradient(135deg, #f7f2e8 0%, #efe7da 48%, #f5efe7 100%);
          }

          .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1220px;
          }

          .app-shell {
            background: rgba(255, 252, 246, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.7);
            border-radius: 30px;
            box-shadow: 0 24px 60px rgba(37, 43, 58, 0.12);
            padding: 1.4rem 1.4rem 1.2rem;
            backdrop-filter: blur(10px);
          }

          .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-size: 0.78rem;
            font-weight: 700;
            color: #0d6b5d;
            margin-bottom: 0.7rem;
          }

          .hero-title {
            font-size: clamp(2.4rem, 4vw, 4rem);
            line-height: 0.98;
            font-weight: 700;
            color: #1d2430;
            margin: 0 0 0.8rem 0;
          }

          .hero-copy {
            color: #687282;
            font-size: 1.06rem;
            line-height: 1.7;
            max-width: 820px;
            margin-bottom: 0.6rem;
          }

          .panel-card {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(29, 36, 48, 0.12);
            border-radius: 24px;
            padding: 1.15rem 1.15rem 1rem;
            min-height: 132px;
          }

          .panel-title {
            font-size: 2rem;
            font-weight: 700;
            color: #1d2430;
            margin: 0 0 0.45rem 0;
          }

          .panel-copy {
            color: #687282;
            font-size: 0.96rem;
            line-height: 1.55;
            margin: 0;
          }

          .section-title {
            font-size: 0.88rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-weight: 700;
            color: #0d6b5d;
            margin: 0 0 0.8rem 0;
          }

          .bubble-wrap {
            display: flex;
            margin-bottom: 0.9rem;
          }

          .bubble-wrap.user {
            justify-content: flex-end;
          }

          .bubble {
            max-width: 88%;
            border-radius: 22px;
            padding: 0.95rem 1rem;
            box-shadow: 0 10px 24px rgba(31, 40, 54, 0.08);
          }

          .bubble.assistant {
            background: #e8f4ee;
            border: 1px solid rgba(13, 107, 93, 0.12);
            border-bottom-left-radius: 10px;
          }

          .bubble.user {
            background: linear-gradient(135deg, #113b5d, #1f587f);
            color: #ffffff;
            border-bottom-right-radius: 10px;
          }

          .bubble-label {
            display: block;
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            opacity: 0.75;
            margin-bottom: 0.35rem;
          }

          .bubble-text {
            margin: 0;
            line-height: 1.65;
            font-size: 0.98rem;
            word-break: break-word;
          }

          .shortlist-card {
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(29, 36, 48, 0.12);
            border-radius: 22px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.85rem;
          }

          .shortlist-name {
            font-size: 1rem;
            font-weight: 700;
            color: #1d2430;
            margin: 0 0 0.35rem 0;
          }

          .pill {
            display: inline-block;
            background: rgba(13, 107, 93, 0.1);
            color: #0d6b5d;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            border-radius: 999px;
            padding: 0.25rem 0.55rem;
            margin-bottom: 0.5rem;
          }

          .small-copy {
            color: #687282;
            font-size: 0.9rem;
            line-height: 1.55;
            margin: 0;
          }

          div[data-testid="stButton"] > button {
            border-radius: 18px;
            border: 1px solid rgba(29, 36, 48, 0.12);
            background: rgba(255, 253, 248, 0.95);
            color: #1d2430;
            font-weight: 700;
            min-height: 3.15rem;
          }

          div[data-testid="stButton"] > button:hover {
            border-color: rgba(13, 107, 93, 0.35);
            color: #0d6b5d;
          }

          div[data-testid="stTextArea"] textarea {
            border-radius: 18px;
            border: 1px solid rgba(29, 36, 48, 0.12);
            background: rgba(255, 255, 255, 0.92);
            min-height: 104px;
          }

          div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.54);
            border: 1px solid rgba(29, 36, 48, 0.1);
            border-radius: 22px;
            padding: 0.8rem 0.8rem 0.2rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.last_response = None


def run_turn(user_text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})
    response = build_response([ChatMessage(**message) for message in st.session_state.messages])
    st.session_state.messages.append({"role": "assistant", "content": response.reply})
    st.session_state.last_response = response


def render_hero() -> None:
    turns = len(st.session_state.messages)
    st.markdown('<div class="eyebrow">SHL Labs Assignment</div>', unsafe_allow_html=True)
    st.markdown(
        '<h1 class="hero-title">Conversational Assessment Recommender</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<p class="hero-copy">'
            "This interactive dashboard sits on top of the assignment logic so an interviewer can test "
            "clarification, refinement, grounded recommendations, and comparison behavior in one place."
            "</p>"
        ),
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(3, gap="small")
    metrics = [
        ("/health", "Readiness check stays available for evaluator workflows."),
        ("/chat", "Stateless conversation handling powers the recommendation flow."),
        (f"{len(CATALOG)} items", f"Current grounded SHL catalog coverage. Turns so far: {turns}."),
    ]

    for column, (title, copy) in zip(metric_cols, metrics):
        with column:
            st.markdown(
                (
                    '<div class="panel-card">'
                    f'<div class="panel-title">{html.escape(title)}</div>'
                    f'<p class="panel-copy">{html.escape(copy)}</p>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def render_chat_history() -> None:
    st.markdown('<div class="section-title">Conversation</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        welcome = (
            "Describe the role you are hiring for, paste a short job description, "
            "or ask me to compare two SHL assessments."
        )
        st.markdown(
            (
                '<div class="bubble-wrap assistant">'
                '<div class="bubble assistant">'
                '<span class="bubble-label">Assistant</span>'
                f'<p class="bubble-text">{html.escape(welcome)}</p>'
                "</div></div>"
            ),
            unsafe_allow_html=True,
        )
        return

    for message in st.session_state.messages:
        role = message["role"]
        label = "User" if role == "user" else "Assistant"
        st.markdown(
            (
                f'<div class="bubble-wrap {role}">'
                f'<div class="bubble {role}">'
                f'<span class="bubble-label">{label}</span>'
                f'<p class="bubble-text">{html.escape(message["content"])}</p>'
                "</div></div>"
            ),
            unsafe_allow_html=True,
        )


def render_composer() -> None:
    with st.form("composer", clear_on_submit=True):
        prompt = st.text_area(
            "Message",
            label_visibility="collapsed",
            placeholder="Example: Hiring a mid-level Java developer who works with stakeholders and needs a balanced shortlist.",
        )
        send = st.form_submit_button("Send")

    if send and prompt.strip():
        run_turn(prompt.strip())
        st.rerun()


def render_recommendations() -> None:
    response = st.session_state.last_response
    st.markdown('<div class="section-title">Latest Shortlist</div>', unsafe_allow_html=True)

    if not response or not response.recommendations:
        st.info("Recommendations will appear here after the agent has enough context.")
        return

    for item in response.recommendations:
        catalog_item = CATALOG_BY_NAME.get(item.name, {})
        details = []
        if catalog_item.get("duration_minutes"):
            details.append(f"Approx. {catalog_item['duration_minutes']} min")
        if catalog_item.get("description"):
            details.append(catalog_item["description"])
        details_text = " ".join(details) if details else "Grounded SHL catalog recommendation."

        st.markdown(
            (
                '<div class="shortlist-card">'
                f'<div class="pill">Type {html.escape(item.test_type)}</div>'
                f'<div class="shortlist-name">{html.escape(item.name)}</div>'
                f'<p class="small-copy">{html.escape(details_text)}</p>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.link_button("Open SHL catalog page", item.url, use_container_width=True)

    if response.end_of_conversation:
        st.success("The agent marked the current recommendation task as complete.")


def render_scenarios() -> None:
    st.markdown('<div class="section-title">Try Scenarios</div>', unsafe_allow_html=True)
    for label, prompt in SCENARIOS.items():
        if st.button(label, use_container_width=True):
            run_turn(prompt)
            st.rerun()

    if st.button("Reset Conversation", use_container_width=True):
        reset_conversation()
        st.rerun()


def render_coverage() -> None:
    st.markdown('<div class="section-title">Coverage</div>', unsafe_allow_html=True)
    st.markdown(
        (
            '<div class="panel-card">'
            '<p class="small-copy">'
            "Clarifies vague prompts, returns grounded SHL recommendations, handles refinements, "
            "compares assessments, and refuses off-topic or prompt-injection requests."
            "</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


init_state()
inject_styles()

st.markdown('<div class="app-shell">', unsafe_allow_html=True)
render_hero()
st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

left, right = st.columns([1.6, 1], gap="large")

with left:
    render_chat_history()
    st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
    render_composer()

with right:
    render_scenarios()
    st.markdown("<div style='height: 0.8rem'></div>", unsafe_allow_html=True)
    render_recommendations()
    st.markdown("<div style='height: 0.8rem'></div>", unsafe_allow_html=True)
    render_coverage()

st.markdown("</div>", unsafe_allow_html=True)
