from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.answer_extraction.document_model import SourceSpan


@dataclass
class AnswerCandidate:
    question_no: int
    raw_answer: str
    normalized_answer: str
    answer_type: str = "unknown"
    source_kind: str = "unknown"
    source_file: str = ""
    source_span: SourceSpan = field(default_factory=SourceSpan)
    evidence_text: str = ""
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_span"] = self.source_span.to_dict()
        return data


@dataclass
class AnswerCandidatePool:
    candidates_by_question: dict[int, list[AnswerCandidate]] = field(default_factory=dict)

    def add(self, candidate: AnswerCandidate) -> None:
        bucket = self.candidates_by_question.setdefault(candidate.question_no, [])
        for existing in bucket:
            if existing.normalized_answer == candidate.normalized_answer:
                existing.confidence = max(existing.confidence, candidate.confidence)
                existing.warnings = sorted(set(existing.warnings + candidate.warnings))
                existing.blocking_errors = sorted(set(existing.blocking_errors + candidate.blocking_errors))
                if not existing.evidence_text and candidate.evidence_text:
                    existing.evidence_text = candidate.evidence_text
                return
        bucket.append(candidate)

    def highest_confidence_candidate(self, question_no: int) -> AnswerCandidate | None:
        bucket = self.candidates_by_question.get(question_no, [])
        if not bucket:
            return None
        return sorted(bucket, key=lambda c: (-c.confidence, c.normalized_answer))[0]

    def question_numbers(self) -> list[int]:
        return sorted(self.candidates_by_question)

    def conflicting_question_numbers(self) -> list[int]:
        conflicts = []
        for question_no, candidates in self.candidates_by_question.items():
            answers = {candidate.normalized_answer for candidate in candidates}
            if len(answers) > 1:
                conflicts.append(question_no)
        return sorted(conflicts)

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {str(k): [candidate.to_dict() for candidate in v] for k, v in sorted(self.candidates_by_question.items())}
