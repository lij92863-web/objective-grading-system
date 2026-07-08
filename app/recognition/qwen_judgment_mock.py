"""Qwen complex-blank judgment mock (Stage R6).

Simulates a Qwen structured judgment for complex math expressions
(equations, inequalities, intervals, etc.) without real API calls.
"""

import dataclasses
from typing import Optional

from .models import QwenJudgmentMock, RecognizedAnswerDraft

# Default auto-accept threshold
_DEFAULT_THRESHOLD = 0.90


def apply_qwen_judgment_mock(
    standard_answer: str,
    student_answer: str,
    question_text: str = "",
    confidence: float = 0.95,
    verdict: str = "correct",
    reason: str = "mock",
    normalized_standard: Optional[str] = None,
    normalized_student: Optional[str] = None,
    equivalence_type: str = "same_value",
    requires_review: bool = False,
) -> QwenJudgmentMock:
    """Create a mock Qwen judgment for a complex blank question.

    This simulates what a real Qwen API call would return.  Every
    parameter has a sensible default so tests and pipelines can create
    various scenarios quickly.

    Parameters
    ----------
    standard_answer:
        The correct answer from the answer key.
    student_answer:
        The student's recognized answer.
    question_text:
        Optional question stem for context.
    confidence:
        Qwen confidence (0.0-1.0).
    verdict:
        One of ``correct``, ``wrong``, ``partial``, ``needs_review``,
        ``invalid``.
    reason:
        Human-readable reason for the verdict.
    normalized_standard:
        Qwen-normalised standard answer.  ``None`` (default) falls back
        to *standard_answer*.
    normalized_student:
        Qwen-normalised student answer.  ``None`` (default) falls back
        to *student_answer*.
    equivalence_type:
        ``same_value``, ``same_solution_set``, ``same_expression``,
        ``format_mismatch``, or ``unknown``.
    requires_review:
        Whether Qwen itself requests teacher review.
    """
    if verdict not in QwenJudgmentMock.VALID_VERDICTS:
        raise ValueError(
            f"verdict must be one of {QwenJudgmentMock.VALID_VERDICTS}, got {verdict!r}"
        )

    if normalized_standard is None:
        normalized_standard = standard_answer
    if normalized_student is None:
        normalized_student = student_answer

    return QwenJudgmentMock(
        verdict=verdict,
        confidence=confidence,
        reason=reason,
        normalized_standard=normalized_standard,
        normalized_student=normalized_student,
        equivalence_type=equivalence_type,
        requires_review=requires_review,
    )


def should_auto_accept_qwen_judgment(
    judgment: QwenJudgmentMock,
    draft: Optional[RecognizedAnswerDraft] = None,
    threshold: float = _DEFAULT_THRESHOLD,
) -> bool:
    """Decide whether a Qwen judgment can be auto-accepted.

    All of the following must be true:

    1. verdict is ``correct``, ``wrong``, or ``partial``.
    2. confidence >= *threshold*.
    3. ``reason`` is not empty.
    4. ``normalized_standard`` is not empty.
    5. ``normalized_student`` is not empty.
    6. The draft (if provided) is not ``low_confidence``.
    7. The draft (if provided) does not have multiple candidate answers.
    8. ``judgment.requires_review`` is ``False``.

    Parameters
    ----------
    judgment:
        The Qwen judgment to evaluate.
    draft:
        The associated recognition draft, if available.
    threshold:
        Minimum confidence for auto-acceptance (default 0.90).
    """
    # 1. verdict must be score-able
    if judgment.verdict not in {
        QwenJudgmentMock.VERDICT_CORRECT,
        QwenJudgmentMock.VERDICT_WRONG,
        QwenJudgmentMock.VERDICT_PARTIAL,
    }:
        return False

    # 2. confidence
    if judgment.confidence < threshold:
        return False

    # 3. reason must be present
    if not (judgment.reason or "").strip():
        return False

    # 4-5. normalised fields
    if not (judgment.normalized_standard or "").strip():
        return False
    if not (judgment.normalized_student or "").strip():
        return False

    # 6. draft must not be low-confidence
    if draft is not None and draft.status == RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE:
        return False

    # 7. draft must not have multiple candidates
    if draft is not None and len(draft.candidate_answers) > 1:
        return False

    # 8. judgment itself requests review
    if judgment.requires_review:
        return False

    return True
