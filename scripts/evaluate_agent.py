from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CASES_PATH = BASE_DIR / "data" / "evaluation_cases.json"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.agent import build_response
from app.catalog import load_catalog
from app.models import ChatMessage


def load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_names(items: list[Any]) -> set[str]:
    return {str(item).strip() for item in items if str(item).strip()}


def evaluate_case(case: dict[str, Any], catalog_urls: set[str]) -> dict[str, Any]:
    messages = [ChatMessage(**message) for message in case["messages"]]
    response = build_response(messages)
    expected = case.get("expected", {})

    recommended_names = [item.name for item in response.recommendations]
    recommended_types = [item.test_type for item in response.recommendations]
    relevant_names = normalize_names(expected.get("relevant_assessments", []))

    grounding_pass = all(item.url in catalog_urls for item in response.recommendations)
    unique_names_pass = len(recommended_names) == len(set(recommended_names))
    size_pass = expected.get("min_recommendations", 0) <= len(response.recommendations) <= expected.get(
        "max_recommendations", 10
    )

    reply_text = response.reply.lower()
    contains_all = all(fragment.lower() in reply_text for fragment in expected.get("reply_contains", []))
    any_fragments = expected.get("reply_any_contains", [])
    contains_any = True if not any_fragments else any(fragment.lower() in reply_text for fragment in any_fragments)

    end_flag = expected.get("end_of_conversation")
    end_pass = True if end_flag is None else response.end_of_conversation is bool(end_flag)

    allowed_types = set(expected.get("allowed_test_types", []))
    forbidden_types = set(expected.get("forbidden_test_types", []))
    allowed_types_pass = True if not allowed_types else all(item in allowed_types for item in recommended_types)
    forbidden_types_pass = all(item not in forbidden_types for item in recommended_types)

    hits = len(relevant_names.intersection(recommended_names))
    recall_at_10 = 1.0 if not relevant_names else hits / len(relevant_names)
    precision_at_10 = 1.0 if not recommended_names else hits / len(recommended_names)

    category = case["category"]
    behavior_pass = all(
        [
            grounding_pass,
            unique_names_pass,
            size_pass,
            contains_all,
            contains_any,
            end_pass,
            allowed_types_pass,
            forbidden_types_pass,
            category_specific_pass(category, response.recommendations),
        ]
    )

    return {
        "id": case["id"],
        "category": category,
        "behavior_pass": behavior_pass,
        "grounding_pass": grounding_pass and unique_names_pass,
        "schema_pass": schema_pass(response),
        "recall_at_10": recall_at_10,
        "precision_at_10": precision_at_10,
        "recommendation_count": len(response.recommendations),
        "recommended_names": recommended_names,
        "reply": response.reply,
        "end_of_conversation": response.end_of_conversation,
        "checks": {
            "size_pass": size_pass,
            "contains_all": contains_all,
            "contains_any": contains_any,
            "end_pass": end_pass,
            "allowed_types_pass": allowed_types_pass,
            "forbidden_types_pass": forbidden_types_pass,
        },
    }


def category_specific_pass(category: str, recommendations: list[Any]) -> bool:
    if category in {"clarify", "compare", "refuse"}:
        return len(recommendations) == 0
    if category == "shortlist":
        return 1 <= len(recommendations) <= 10
    return True


def schema_pass(response: Any) -> bool:
    return (
        isinstance(response.reply, str)
        and isinstance(response.recommendations, list)
        and isinstance(response.end_of_conversation, bool)
        and all(hasattr(item, "name") and hasattr(item, "url") and hasattr(item, "test_type") for item in response.recommendations)
    )


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    shortlist_results = [result for result in results if result["category"] == "shortlist"]
    return {
        "case_count": len(results),
        "schema_pass_rate": mean(int(result["schema_pass"]) for result in results),
        "grounding_pass_rate": mean(int(result["grounding_pass"]) for result in results),
        "behavior_pass_rate": mean(int(result["behavior_pass"]) for result in results),
        "mean_recall_at_10": mean(result["recall_at_10"] for result in shortlist_results) if shortlist_results else 0.0,
        "mean_precision_at_10": mean(result["precision_at_10"] for result in shortlist_results) if shortlist_results else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the SHL conversational recommender on labeled local cases.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Path to a JSON file with labeled evaluation cases.",
    )
    args = parser.parse_args()

    cases = load_cases(args.cases)
    catalog_urls = {item["url"] for item in load_catalog()}
    results = [evaluate_case(case, catalog_urls) for case in cases]
    summary = aggregate(results)

    print("=== Evaluation Summary ===")
    print(json.dumps(summary, indent=2))
    print("\n=== Per-case Results ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
