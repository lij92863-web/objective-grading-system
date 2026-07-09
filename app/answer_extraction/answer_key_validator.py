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


def enforce_evidence_required(candidate, proposed_status: str) -> tuple[str, list[str], list[dict[str, object]]]:
    if proposed_status in {"accepted", "accepted_with_warnings"} and not candidate.evidence_text:
        return "needs_review", ["missing_evidence_for_accepted_answer"], [
            {"type": "missing_evidence_for_accepted_answer", "question_no": candidate.question_no}
        ]
    return proposed_status, [], []


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
        if candidate.source_kind == "llm_candidate":
            warnings.append("llm_candidate_used")
            review_items.append({"type": "llm_candidate_requires_review", "question_no": question_no})
            proposed = "needs_review"
            statuses[question_no] = proposed
            continue
        if question.question_type == "single_choice" and len(candidate.normalized_answer) > 1:
            blocking.append("single_choice_multi_answer")
            proposed = "blocked"
        elif question.question_type == "multi_choice" and len(candidate.normalized_answer) == 1:
            warnings.append("multi_choice_single_letter")
            proposed = "accepted_with_warnings"
        elif question.question_type == "blank" and candidate.normalized_answer:
            if candidate.normalized_answer in {"A", "B", "C", "D"}:
                review_items.append({"type": "question_type_mismatch", "question_no": question_no})
                proposed = "needs_review"
            else:
                warnings.append("fill_answer_low_confidence")
                proposed = "accepted_with_warnings"
        elif question.question_type in {"solution", "unknown"} and candidate.normalized_answer in {"A", "B", "C", "D"}:
            review_items.append({"type": "question_type_mismatch", "question_no": question_no})
            proposed = "needs_review"
        else:
            proposed = "accepted"
        final_status, evidence_warnings, evidence_reviews = enforce_evidence_required(candidate, proposed)
        warnings.extend(evidence_warnings)
        review_items.extend(evidence_reviews)
        statuses[question_no] = final_status
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
