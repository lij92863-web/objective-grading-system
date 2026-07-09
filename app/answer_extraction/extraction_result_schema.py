from __future__ import annotations


REQUIRED_RESULT_FIELDS = {
    "schema_version",
    "run_id",
    "strategy",
    "status",
    "question_count",
    "answer_count",
    "accepted_count",
    "review_count",
    "blocked_count",
    "answers",
    "review_items",
    "blocking_errors",
    "warnings",
    "diagnostics",
}


def with_schema_defaults(result: dict[str, object]) -> dict[str, object]:
    updated = dict(result)
    updated.setdefault("schema_version", "answer_extraction.v3")
    updated.setdefault("blocked_count", len(updated.get("blocking_errors", []) or []))
    updated.setdefault("warnings", [])
    updated.setdefault("diagnostics", {})
    return updated
