from __future__ import annotations

from dataclasses import dataclass, field

from app.answer_extraction.text_normalizer import compact_choice_text, normalize_text


VALID_CHOICES = set("ABCD")


@dataclass(frozen=True)
class NormalizedAnswer:
    raw_answer: str
    normalized_answer: str
    answer_type: str
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.blocking_errors


def normalize_answer(raw_answer: str, question_type: str = "unknown") -> NormalizedAnswer:
    raw = raw_answer or ""
    cleaned = normalize_text(raw)
    if question_type in {"blank", "fill_blank"}:
        return NormalizedAnswer(raw, cleaned, "blank")
    compact = compact_choice_text(cleaned)
    if not compact:
        return NormalizedAnswer(raw, "", "unknown", warnings=["empty_answer"])
    if any(ch not in VALID_CHOICES for ch in compact):
        return NormalizedAnswer(raw, compact, "unknown", blocking_errors=["invalid_answer_token"])
    normalized = "".join(sorted(set(compact)))
    answer_type = "single_choice" if len(normalized) == 1 else "multi_choice"
    return NormalizedAnswer(raw, normalized, answer_type)
