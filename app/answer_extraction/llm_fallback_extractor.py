from __future__ import annotations

from dataclasses import dataclass

from app.answer_extraction.answer_candidate_pool import AnswerCandidate
from app.answer_extraction.answer_normalizer import normalize_answer


@dataclass(frozen=True)
class LlmFallbackConfig:
    enabled: bool = False


class LlmFallbackExtractor:
    def __init__(self, config: LlmFallbackConfig | None = None) -> None:
        self.config = config or LlmFallbackConfig()

    def extract_candidate(self, snippet: str, question_no: int, raw_answer: str, evidence_text: str) -> AnswerCandidate | None:
        if not self.config.enabled:
            return None
        if not evidence_text or evidence_text not in snippet:
            return None
        normalized = normalize_answer(raw_answer)
        return AnswerCandidate(
            question_no=question_no,
            raw_answer=raw_answer,
            normalized_answer=normalized.normalized_answer,
            answer_type=normalized.answer_type,
            source_kind="llm_candidate",
            evidence_text=evidence_text,
            confidence=0.7 if normalized.is_valid else 0.0,
            warnings=["llm_candidate_requires_review"],
            blocking_errors=normalized.blocking_errors,
        )
