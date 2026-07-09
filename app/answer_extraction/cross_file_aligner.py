from __future__ import annotations

from dataclasses import dataclass, field

from app.answer_extraction.answer_candidate_pool import AnswerCandidatePool
from app.answer_extraction.question_index_builder import QuestionIndex


@dataclass
class AlignmentResult:
    missing_answers: list[int] = field(default_factory=list)
    unexpected_answers: list[int] = field(default_factory=list)
    duplicate_answers: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "missing_answers": list(self.missing_answers),
            "unexpected_answers": list(self.unexpected_answers),
            "duplicate_answers": list(self.duplicate_answers),
            "warnings": list(self.warnings),
            "blocking_errors": list(self.blocking_errors),
        }


def align_by_question_no(question_index: QuestionIndex, candidate_pool: AnswerCandidatePool) -> AlignmentResult:
    question_numbers = set(question_index.question_numbers())
    answer_numbers = set(candidate_pool.question_numbers())
    result = AlignmentResult()
    result.missing_answers = sorted(question_numbers - answer_numbers)
    result.unexpected_answers = sorted(answer_numbers - question_numbers) if question_numbers else sorted(answer_numbers)
    result.duplicate_answers = candidate_pool.conflicting_question_numbers()
    if result.missing_answers:
        result.warnings.append("missing_answer")
    if result.unexpected_answers:
        result.blocking_errors.append("unexpected_answer_number")
    if result.duplicate_answers:
        result.blocking_errors.append("duplicate_conflicting_answer")
    if "question_number_rewind" in question_index.blocking_errors:
        result.blocking_errors.append("question_number_rewind")
    return result
