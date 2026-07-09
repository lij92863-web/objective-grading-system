"""Simple score rows builder - matches legacy ``simple_score_rows``."""

from collections import defaultdict


def _get(value, name, default=None):
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _competition_ranks(results: list) -> list:
    sorted_results = sorted(
        enumerate(results),
        key=lambda item: (-_get(item[1], "score"), item[0]),
    )
    ranks = [0 for _ in results]
    previous_score = None
    current_rank = 0
    for position, (index, result) in enumerate(sorted_results, start=1):
        score = _get(result, "score")
        if previous_score is None or score != previous_score:
            current_rank = position
        ranks[index] = current_rank
        previous_score = score
    return ranks


def build_simple_score_rows(results: list) -> list:
    ranks = _competition_ranks(results)
    rows = []
    for index, result in enumerate(results):
        details = _get(result, "details", [])
        by_status = defaultdict(list)
        for detail in details:
            by_status[_get(detail, "status", "")].append(
                str(_get(detail, "number", _get(detail, "question", "")))
            )

        percent = _get(result, "percent", 0)
        remarks = []
        if percent >= 90:
            remarks.append("优秀")
        elif percent < 60:
            remarks.append("未及格")
        if by_status.get("blank"):
            remarks.append("有空白")
        if by_status.get("invalid") or by_status.get("unrecognized"):
            remarks.append("有异常")

        rows.append({
            "rank": ranks[index],
            "student_id": _get(result, "student_id"),
            "name": _get(result, "name", ""),
            "score": _get(result, "score"),
            "max_score": _get(result, "max_score", 0),
            "percent": _get(result, "percent", 0),
            "correct_count": _get(result, "correct_count", 0),
            "wrong_or_partial_count": _get(
                result, "wrong_or_partial_count", 0
            ),
            "blank_count": _get(result, "blank_count", 0),
            "invalid_count": _get(result, "invalid_count", 0),
            "wrong_questions": ";".join(
                by_status.get("wrong", []) + by_status.get("invalid", [])
            ),
            "blank_questions": ";".join(by_status.get("blank", [])),
            "remark": "；".join(remarks) if remarks else "",
        })
    return rows
