from __future__ import annotations

from dataclasses import dataclass, field

from app.answer_extraction.answer_candidate_pool import AnswerCandidatePool
from app.answer_extraction.cross_file_aligner import AlignmentResult
from app.answer_extraction.question_index_builder import QuestionIndex


@dataclass
class ValidationReport:
    status: str
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)
    review_items: list[dict[str, object]] = field(default_factory=list)
    answer_statuses: dict[int, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "warnings": list(self.warnings),
            "blocking_errors": list(self.blocking_errors),
            "review_items": list(self.review_items),
            "answer_statuses": {str(k): v for k, v in sorted(self.answer_statuses.items())},
        }


def validate_answer_key(question_index: QuestionIndex, candidate_pool: AnswerCandidatePool, alignment: AlignmentResult) -> ValidationReport:
    warnings = list(alignment.warnings)
    blocking = list(alignment.blocking_errors)
    review_items: list[dict[str, object]] = []
    statuses: dict[int, str] = {}
    by_question = question_index.by_number()
    for question_no in sorted(set(question_index.question_numbers()) & set(candidate_pool.question_numbers())):
        question = by_question[question_no]
        candidate = candidate_pool.highest_confidence_candidate(question_no)
        if not candidate:
            continue
        if candidate.blocking_errors:
            blocking.extend(candidate.blocking_errors)
        if statuses.get(question_no) == "accepted" and not candidate.evidence_text:
            review_items.append({"type": "missing_evidence", "question_no": question_no})
        if candidate.source_kind == "llm_candidate":
            warnings.append("llm_candidate_used")
            review_items.append({"type": "llm_candidate_requires_review", "question_no": question_no})
            statuses[question_no] = "needs_review"
            continue
        if question.question_type == "single_choice" and len(candidate.normalized_answer) > 1:
            blocking.append("single_choice_multi_answer")
            statuses[question_no] = "blocked"
        elif question.question_type == "multi_choice" and len(candidate.normalized_answer) == 1:
            warnings.append("multi_choice_single_letter")
            statuses[question_no] = "accepted_with_warnings"
        elif question.question_type == "blank" and candidate.normalized_answer:
            if candidate.normalized_answer in {"A", "B", "C", "D"}:
                review_items.append({"type": "question_type_mismatch", "question_no": question_no})
                statuses[question_no] = "needs_review"
            else:
                warnings.append("fill_answer_low_confidence")
                statuses[question_no] = "accepted_with_warnings"
        elif question.question_type in {"solution", "unknown"} and candidate.normalized_answer in {"A", "B", "C", "D"}:
            review_items.append({"type": "question_type_mismatch", "question_no": question_no})
            statuses[question_no] = "needs_review"
        else:
            statuses[question_no] = "accepted"
    for question_no in alignment.missing_answers:
        review_items.append({"type": "missing_answer", "question_no": question_no})
    for question_no in candidate_pool.conflicting_question_numbers():
        review_items.append({"type": "conflicting_candidates", "question_no": question_no})
    blocking = sorted(set(blocking))
    warnings = sorted(set(warnings))
    if blocking:
        status = "blocked"
    elif review_items:
        status = "needs_review"
    elif warnings:
        status = "accepted_with_warnings"
    else:
        status = "accepted"
    return ValidationReport(status, warnings, blocking, review_items, statuses)
