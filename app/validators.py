"""Data quality checks and blocking-error policy."""

from typing import Dict, Iterable

from legacy.objective_grader_legacy import build_validation_report, write_validation_report


BLOCKING_SCOPES = {
    "answer_key",
    "submission",
    "submissions",
    "student_match",
    "recognized_submissions",
    "input",
    "class",
}


def is_blocking_error(row: Dict[str, object]) -> bool:
    severity = str(row.get("severity", "")).strip().lower()
    if severity not in {"error", "blocking"}:
        return False
    scope = str(row.get("scope", "")).strip().lower()
    return not scope or scope in BLOCKING_SCOPES


def has_blocking_errors(validation_rows: Iterable[Dict[str, object]]) -> bool:
    return any(is_blocking_error(row) for row in validation_rows)

