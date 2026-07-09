"""Item statistics builder matching legacy ``item_stats``.

This module is pure application logic: it reads legacy-shaped objects or dicts
without importing legacy and returns rows for Excel/HTML exporters.
"""

from collections import Counter
from typing import Any, Iterable


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _questions(answer_key: Any) -> Iterable[Any]:
    if isinstance(answer_key, dict):
        return answer_key.get("questions", [])
    return getattr(answer_key, "questions", answer_key)


def _details(result: Any) -> Iterable[Any]:
    return _get(result, "details", []) or []


def _format_answer(answer: Any) -> str:
    if answer is None:
        return ""
    if isinstance(answer, str):
        return "".join(sorted(answer))
    return "".join(sorted(str(token) for token in answer))


def _format_expected_answer(spec: Any) -> str:
    answer_aliases = _get(spec, "answer_aliases", ()) or ()
    tolerance = _get(spec, "tolerance")
    answer_text = _get(spec, "answer_text", "") or ""
    if answer_aliases or tolerance is not None:
        return answer_text
    return _format_answer(_get(spec, "answers", _get(spec, "answer", "")))


def _tags(spec: Any) -> str:
    tags = _get(spec, "tags", ()) or ()
    if isinstance(tags, str):
        return tags
    return ";".join(str(tag) for tag in tags)


def build_item_stats(answer_key: Any, results: list) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in _questions(answer_key):
        number = _get(spec, "number", _get(spec, "question"))
        details = [
            detail
            for result in results
            for detail in _details(result)
            if _get(detail, "number", _get(detail, "question")) == number
        ]
        total = len(details) or 1
        correct = sum(
            1 for detail in details
            if _get(detail, "status") in {"correct", "bonus"}
        )
        partial = sum(
            1 for detail in details if _get(detail, "status") == "partial"
        )
        blank = sum(
            1 for detail in details if _get(detail, "status") == "blank"
        )
        invalid = sum(
            1 for detail in details if _get(detail, "status") == "invalid"
        )
        wrong = sum(
            1 for detail in details
            if _get(detail, "status") in {"wrong", "invalid", "unrecognized"}
        )
        distribution = Counter(
            _format_answer(_get(detail, "actual")) or "(blank)"
            for detail in details
        )
        rows.append({
            "question": number,
            "tags": _tags(spec),
            "answer": _format_expected_answer(spec),
            "accuracy": round(correct / total * 100, 2),
            "blank_rate": round(blank / total * 100, 2),
            "invalid_rate": round(invalid / total * 100, 2),
            "wrong_rate": round(wrong / total * 100, 2),
            "partial_rate": round(partial / total * 100, 2),
            "mistake_count": wrong + partial,
            "distribution": dict(distribution),
        })
    return rows
