"""Conservative single-choice candidate generation."""

from app.student_recognition.errors.error_codes import ErrorCode

from .omr_candidate import RecognizedAnswerCandidate
from .omr_policy import DEFAULT_OMR_POLICY

_REVIEW_CLASSIFICATIONS = ("weak", "erased", "dirty", "ambiguous")


def recognize_single_choice(
    question_no,
    metrics,
    evidence=(),
    policy=DEFAULT_OMR_POLICY,
):
    strong = [metric for metric in metrics if metric.classification == "strong"]
    if len(strong) > 1:
        return RecognizedAnswerCandidate(
            question_no, (), "needs_review",
            (ErrorCode.OMR_MULTI_MARK_SINGLE_CHOICE,), tuple(evidence),
        )
    classifications = {metric.classification for metric in metrics}
    if classifications & set(_REVIEW_CLASSIFICATIONS):
        if "weak" in classifications:
            reason = ErrorCode.OMR_WEAK_MARK
        elif "erased" in classifications:
            reason = ErrorCode.OMR_ERASURE_DETECTED
        elif "dirty" in classifications:
            reason = ErrorCode.OMR_BORDER_NOISE_HIGH
        else:
            reason = ErrorCode.OMR_LOW_CONFIDENCE
        return RecognizedAnswerCandidate(
            question_no, (), "needs_review",
            (reason,), tuple(evidence),
        )

    ranked = sorted(metrics, key=lambda metric: metric.mark_score, reverse=True)
    if not ranked or ranked[0].classification == "blank":
        return RecognizedAnswerCandidate(
            question_no, (), "blank_candidate",
            (ErrorCode.OMR_EMPTY_MARK,), tuple(evidence),
        )
    second_score = ranked[1].mark_score if len(ranked) > 1 else 0.0
    safely_selected = (
        ranked[0].mark_score >= policy.selected_threshold
        and ranked[0].mark_score - second_score >= policy.single_choice_margin
        and second_score < policy.weak_threshold
    )
    if safely_selected:
        return RecognizedAnswerCandidate(
            question_no, (ranked[0].option,), "auto_candidate", (), tuple(evidence)
        )
    return RecognizedAnswerCandidate(
        question_no, (), "needs_review",
        (ErrorCode.OMR_LOW_CONFIDENCE,), tuple(evidence),
    )
