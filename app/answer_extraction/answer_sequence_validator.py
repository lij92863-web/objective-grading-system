from __future__ import annotations

from dataclasses import dataclass, field

from app.answer_extraction.answer_candidate_pool import AnswerCandidatePool


@dataclass(frozen=True)
class AnswerSequenceValidationResult:
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)


def validate_answer_sequence(pool: AnswerCandidatePool, expected_numbers: set[int] | None = None) -> AnswerSequenceValidationResult:
    warnings: list[str] = []
    blocking: list[str] = []
    for question_no, candidates in pool.candidates_by_question.items():
        answers = {candidate.normalized_answer for candidate in candidates}
        if len(candidates) > 1 and len(answers) == 1:
            warnings.append("duplicate_same_answer")
        if len(answers) > 1:
            blocking.append("duplicate_conflicting_answer")
        if expected_numbers is not None and question_no not in expected_numbers:
            blocking.append("unexpected_answer_number")
    if expected_numbers is not None:
        missing = expected_numbers - set(pool.question_numbers())
        if missing:
            warnings.append("missing_answer_number")
    return AnswerSequenceValidationResult(sorted(set(warnings)), sorted(set(blocking)))
