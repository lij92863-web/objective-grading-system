from __future__ import annotations

from dataclasses import dataclass

from app.answer_extraction.answer_normalizer import normalize_answer


@dataclass(frozen=True)
class FillBlankAnswerDecision:
    normalized_answer: str
    needs_review: bool
    warning: str = ""


def classify_fill_blank_answer(raw_answer: str) -> FillBlankAnswerDecision:
    normalized = normalize_answer(raw_answer, "blank").normalized_answer
    if normalized in {"A", "B", "C", "D"}:
        return FillBlankAnswerDecision(normalized, True, "blank_pure_choice_review")
    return FillBlankAnswerDecision(normalized, False, "fill_answer_low_confidence")
