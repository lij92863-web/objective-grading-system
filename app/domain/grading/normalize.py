"""Answer normalization helpers shared by all grading rules."""

import re
from typing import FrozenSet, Optional, Set

from .models import QuestionSpec

OPTION_RE = re.compile(r"[A-Z0-9]+")
QUESTION_RE = re.compile(r"^(?:q|question|\u9898)?\s*0*(\d+)$", re.IGNORECASE)
CHOICE_OPTIONS = set("ABCDEFGH")
EPSILON = 1e-9


def normalize_answer(value: object) -> FrozenSet[str]:
    """Normalize AC, A,C, a c, and full-width separators into option tokens."""
    if value is None:
        return frozenset()
    text = str(value).strip().upper()
    if not text:
        return frozenset()
    text = (
        text.replace("\uff0c", ",")
        .replace("\uff1b", ";")
        .replace("\u3001", ",")
        .replace("|", ",")
        .replace("/", ",")
    )
    tokens = OPTION_RE.findall(text)
    if len(tokens) == 1 and len(tokens[0]) > 1 and tokens[0].isalpha():
        tokens = list(tokens[0])
    return frozenset(token for token in tokens if token)


def format_answer(answer: FrozenSet[str]) -> str:
    return "".join(sorted(answer))


def parse_question_number(header: str) -> Optional[int]:
    match = QUESTION_RE.match(str(header).strip())
    return int(match.group(1)) if match else None


def allowed_options(spec: QuestionSpec) -> Set[str]:
    return CHOICE_OPTIONS | set(spec.answers)


def is_choice_answer(answer: FrozenSet[str]) -> bool:
    return bool(answer) and all(token in CHOICE_OPTIONS for token in answer)


def is_choice_like_answer(spec: QuestionSpec) -> bool:
    return is_choice_answer(spec.answers) and any(char.isalpha() for char in spec.answer_text.upper())


def format_expected_answer(spec: QuestionSpec) -> str:
    return spec.answer_text if (spec.answer_aliases or spec.tolerance is not None) else format_answer(spec.answers)


def normalize_text_answer(value: object) -> str:
    return str(value or "").strip().replace("\uff0c", ",").replace("\uff1b", ";").replace("\u3000", " ").lower()


def numeric_value(value: object) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    fraction = re.fullmatch(r"\\frac\{([-+]?\d+(?:\.\d+)?)\}\{([-+]?\d+(?:\.\d+)?)\}", text)
    if fraction:
        denominator = float(fraction.group(2))
        return float(fraction.group(1)) / denominator if denominator else None
    simple_fraction = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)/([-+]?\d+(?:\.\d+)?)", text)
    if simple_fraction:
        denominator = float(simple_fraction.group(2))
        return float(simple_fraction.group(1)) / denominator if denominator else None
    try:
        return float(text)
    except ValueError:
        return None


def matches_text_answer(spec: QuestionSpec, raw_actual: str) -> bool:
    actual_text = normalize_text_answer(raw_actual)
    if not actual_text:
        return False
    accepted = [spec.answer_text] + list(spec.answer_aliases)
    for answer in accepted:
        if actual_text == normalize_text_answer(answer):
            return True
    if spec.tolerance is not None:
        actual_number = numeric_value(raw_actual)
        expected_numbers = [numeric_value(answer) for answer in accepted]
        if actual_number is not None:
            for expected_number in expected_numbers:
                if expected_number is not None and abs(actual_number - expected_number) <= spec.tolerance + EPSILON:
                    return True
    return False
