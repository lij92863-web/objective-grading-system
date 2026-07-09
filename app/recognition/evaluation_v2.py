"""R40B: Recognition evaluation v2."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .contracts import RecognitionRunResult


@dataclass
class EvaluationReport:
    total_items: int = 0
    auto_accepted_count: int = 0
    needs_review_count: int = 0
    blocking_count: int = 0
    auto_accept_rate: float = 0.0
    review_rate: float = 0.0
    blocking_rate: float = 0.0
    gold_available: bool = False
    candidate_accuracy: Optional[float] = None
    false_auto_accept_count: Optional[int] = None
    false_auto_accept_rate: Optional[float] = None
    identity_conflict_count: int = 0
    identity_missing_count: int = 0
    invalid_option_count: int = 0
    engine_error_count: int = 0
    malformed_response_count: int = 0
    omr_qwen_conflict_count: int = 0
    blank_low_confidence_count: int = 0
    missing_roi_count: int = 0
    warnings: List[str] = field(default_factory=list)


def evaluate_recognition(result: RecognitionRunResult,
                          gold_answers: Optional[Dict[int, str]] = None) -> EvaluationReport:
    report = EvaluationReport(gold_available=gold_answers is not None)
    if not result.drafts:
        return report
    decisions = result.drafts[0].decisions
    report.total_items = len(decisions)
    for d in decisions:
        if d.status == "auto_accepted": report.auto_accepted_count += 1
        if d.needs_review: report.needs_review_count += 1
        if d.blocking: report.blocking_count += 1
        if d.status == "invalid" or d.reason == "invalid_option": report.invalid_option_count += 1
        if d.status == "engine_error" or d.reason in ("engine_error", "qwen_malformed"):
            report.engine_error_count += 1
        if d.status == "blank" or d.reason in ("blank_low_confidence",):
            report.blank_low_confidence_count += 1
    if report.total_items:
        report.auto_accept_rate = round(report.auto_accepted_count / report.total_items * 100, 2)
        report.review_rate = round(report.needs_review_count / report.total_items * 100, 2)
        report.blocking_rate = round(report.blocking_count / report.total_items * 100, 2)
    if gold_answers:
        def _gold(qn): return gold_answers.get(qn) or gold_answers.get(str(qn))
        correct = sum(1 for d in decisions if _gold(d.question_number)
                      and d.value == _gold(d.question_number))
        report.candidate_accuracy = round(correct / report.total_items * 100, 2) if report.total_items else 0.0
        false_auto = sum(1 for d in decisions if d.status == "auto_accepted"
                         and _gold(d.question_number)
                         and d.value != _gold(d.question_number))
        report.false_auto_accept_count = false_auto
        report.false_auto_accept_rate = round(false_auto / report.total_items * 100, 2) if report.total_items else 0.0
    return report
