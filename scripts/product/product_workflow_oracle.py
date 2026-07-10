"""Small independent truth comparator for the deterministic product benchmark."""

import math
from collections import Counter
from typing import Iterable, Mapping


IDENTITY_FIELDS = ("student_no", "student_name")
NUMERIC_FIELDS = ("score", "max_score", "percent")


def compare_final_scores(
    expected_rows: Iterable[Mapping[str, object]],
    actual_rows: Iterable[Mapping[str, object]],
) -> dict[str, int]:
    expected = list(expected_rows)
    actual = list(actual_rows)
    expected_by_id = {
        str(row["student_id"]): row
        for row in expected
        if bool(row.get("included", True))
    }
    actual_counts = Counter(str(row.get("student_id") or "") for row in actual)
    actual_ids = set(actual_counts)
    expected_ids = set(expected_by_id)
    missing_ids = expected_ids - actual_ids
    unexpected_ids = actual_ids - expected_ids

    wrong_binding = 0
    wrong_score = 0
    wrong_max = 0
    wrong_percent = 0
    invalid_range = 0
    wrong_records = 0
    for row in actual:
        student_id = str(row.get("student_id") or "")
        truth = expected_by_id.get(student_id)
        record_wrong = student_id in unexpected_ids or actual_counts[student_id] > 1
        if truth is not None:
            binding_wrong = any(row.get(field) != truth.get(field) for field in IDENTITY_FIELDS)
            score_wrong = not _same_number(row.get("score"), truth.get("score"))
            max_wrong = not _same_number(row.get("max_score"), truth.get("max_score"))
            percent_wrong = not _same_number(row.get("percent"), truth.get("percent"))
            wrong_binding += int(binding_wrong)
            wrong_score += int(score_wrong)
            wrong_max += int(max_wrong)
            wrong_percent += int(percent_wrong)
            record_wrong = record_wrong or any(
                (binding_wrong, score_wrong, max_wrong, percent_wrong)
            )
        range_wrong = not _valid_range(row)
        invalid_range += int(range_wrong)
        record_wrong = record_wrong or range_wrong
        wrong_records += int(record_wrong)

    duplicate_count = sum(count - 1 for count in actual_counts.values() if count > 1)
    return {
        "expected_final_score_count": len(expected_by_id),
        "actual_final_score_count": len(actual),
        "missing_final_score_count": len(missing_ids),
        "unexpected_final_score_count": len(unexpected_ids),
        "duplicate_final_score_count": duplicate_count,
        "wrong_student_binding_count": wrong_binding,
        "wrong_score_count": wrong_score,
        "wrong_max_score_count": wrong_max,
        "wrong_percent_count": wrong_percent,
        "invalid_score_range_count": invalid_range,
        "wrong_finalized_count": wrong_records + len(missing_ids),
    }


def _same_number(actual: object, expected: object) -> bool:
    try:
        left, right = float(actual), float(expected)
    except (TypeError, ValueError):
        return False
    return math.isfinite(left) and math.isfinite(right) and math.isclose(
        left, right, rel_tol=0.0, abs_tol=1e-9
    )


def _valid_range(row: Mapping[str, object]) -> bool:
    try:
        score = float(row.get("score"))
        maximum = float(row.get("max_score"))
        percent = float(row.get("percent"))
    except (TypeError, ValueError):
        return False
    return (
        all(math.isfinite(value) for value in (score, maximum, percent))
        and maximum >= 0
        and 0 <= score <= maximum
        and 0 <= percent <= 100
        and (maximum != 0 or (score == 0 and percent == 0))
    )
