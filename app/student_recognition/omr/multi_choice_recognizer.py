"""Conservative multi-choice candidate generation."""

from app.student_recognition.errors.error_codes import ErrorCode

from .ambiguity_detector import in_ambiguous_band
from .omr_candidate import RecognizedAnswerCandidate
from .omr_policy import DEFAULT_OMR_POLICY

_REVIEW_CLASSIFICATIONS = ("weak", "erased", "dirty", "ambiguous")


def recognize_multi_choice(
    question_no,
    metrics,
    evidence=(),
    policy=DEFAULT_OMR_POLICY,
):
    uncertain = any(
        metric.classification in _REVIEW_CLASSIFICATIONS
        or in_ambiguous_band(metric.mark_score, policy)
        for metric in metrics
    )
    if uncertain:
        return RecognizedAnswerCandidate(
            question_no, (), "needs_review",
            (ErrorCode.OMR_AMBIGUOUS_MULTI_CHOICE,), tuple(evidence),
        )
    selected = tuple(
        sorted(
            metric.option
            for metric in metrics
            if metric.classification == "strong"
            and metric.mark_score >= policy.selected_threshold
        )
    )
    if not selected:
        return RecognizedAnswerCandidate(
            question_no, (), "blank_candidate",
            (ErrorCode.OMR_EMPTY_MARK,), tuple(evidence),
        )
    return RecognizedAnswerCandidate(
        question_no, selected, "auto_candidate", (), tuple(evidence)
    )
