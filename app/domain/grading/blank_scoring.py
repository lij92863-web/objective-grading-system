"""Fill-in-the-blank grading rules.

These rules intentionally stay deterministic. Ambiguous math expressions are
flagged for teacher review instead of guessed by AI.
"""

import re
from fractions import Fraction
from typing import Iterable, Optional, Set, Tuple

from .normalize import normalize_text_answer, numeric_value

REVIEW_MARKERS = ("<", ">", "\u2264", "\u2265", "\u03c0", "sin", "cos", "tan", "log", "ln", "=")


def canonical_blank_text(value: object) -> str:
    text = normalize_text_answer(value)
    text = text.replace(" ", "")
    text = text.replace("\uff08", "(").replace("\uff09", ")")
    text = text.replace("\u221a", "sqrt")
    text = text.replace("\u6839\u53f7", "sqrt")
    text = re.sub(r"\bsqrt\(([^)]+)\)", r"sqrt\1", text)
    return text


def _fraction(value: str) -> Optional[Fraction]:
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        number = numeric_value(value)
        if number is None:
            return None
        return Fraction(str(number)).limit_denominator(1000000)


def _split_alternatives(value: str) -> Tuple[str, ...]:
    value = value.replace("\u6216", "|").replace(";", "|")
    return tuple(part for part in (item.strip() for item in value.split("|")) if part)


def _parse_set(value: str) -> Optional[Set[str]]:
    if not ((value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]"))):
        return None
    inner = value[1:-1]
    if not inner:
        return set()
    return {canonical_blank_text(part) for part in re.split(r"[,，、]", inner) if part.strip()}


def _looks_like_root(value: str) -> bool:
    return bool(re.fullmatch(r"sqrt[-+]?\d+(?:\.\d+)?", value) or re.fullmatch(r"sqrt\([-+]?\d+(?:\.\d+)?\)", value))


def _same_single(expected: str, actual: str) -> bool:
    if expected == actual:
        return True
    expected_number = _fraction(expected)
    actual_number = _fraction(actual)
    if expected_number is not None and actual_number is not None:
        return expected_number == actual_number
    expected_set = _parse_set(expected)
    actual_set = _parse_set(actual)
    if expected_set is not None and actual_set is not None:
        return expected_set == actual_set
    if _looks_like_root(expected) and _looks_like_root(actual):
        return expected == actual
    return False


def is_review_needed(*values: str) -> bool:
    for value in values:
        lowered = value.lower()
        if any(marker in lowered for marker in REVIEW_MARKERS):
            return True
        if re.search(r"[\(\)]", lowered) and not _looks_like_root(lowered):
            return True
    return False


def blank_answer_matches(expected_values: Iterable[str], actual_value: str) -> Tuple[bool, bool]:
    actual = canonical_blank_text(actual_value)
    candidates = []
    for expected in expected_values:
        candidates.extend(_split_alternatives(canonical_blank_text(expected)))
    for expected in candidates:
        if _same_single(expected, actual):
            return True, False
    return False, is_review_needed(actual, *candidates)
