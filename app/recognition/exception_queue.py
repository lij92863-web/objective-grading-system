"""Exception queue builder for the recognition pipeline (Stage R7).

Collects drafts and judgments that require teacher review and returns
human-readable exception items.
"""

from typing import Iterable, List, Optional

from .models import (
    QwenJudgmentMock,
    RecognitionException,
    RecognizedAnswerDraft,
    StudentIdentityCandidate,
)


def build_exception_queue(
    drafts: Iterable[RecognizedAnswerDraft],
    identity: Optional[StudentIdentityCandidate] = None,
    judgments: Optional[Iterable[QwenJudgmentMock]] = None,
    judgment_threshold: float = 0.90,
) -> List[RecognitionException]:
    """Build the exception queue from recognition drafts and judgments.

    Parameters
    ----------
    drafts:
        All ``RecognizedAnswerDraft`` items from the pipeline.
    identity:
        The parsed student identity, if available.
    judgments:
        Qwen judgments for complex blank questions.
    judgment_threshold:
        Confidence threshold below which a judgment is flagged.
    """
    queue: List[RecognitionException] = []

    # -- identity exceptions -------------------------------------------------
    if identity is not None:
        if identity.status == StudentIdentityCandidate.STATUS_CONFLICT:
            queue.append(
                RecognitionException(
                    code="IDENTITY_CONFLICT",
                    level=RecognitionException.LEVEL_REVIEW,
                    message=identity.message or "姓名栏识别结果与学生名单不一致，请确认。",
                    student_id=identity.matched_student_id,
                    student_name=identity.student_name,
                    source="identity_parser",
                )
            )
        elif identity.status == StudentIdentityCandidate.STATUS_NEEDS_REVIEW:
            queue.append(
                RecognitionException(
                    code="IDENTITY_NEEDS_REVIEW",
                    level=RecognitionException.LEVEL_REVIEW,
                    message=identity.message or "姓名栏识别结果需要确认。",
                    student_id=identity.matched_student_id,
                    student_name=identity.student_name,
                    source="identity_parser",
                )
            )
        elif identity.status == StudentIdentityCandidate.STATUS_INVALID:
            queue.append(
                RecognitionException(
                    code="IDENTITY_INVALID",
                    level=RecognitionException.LEVEL_BLOCKING,
                    message=identity.message or "姓名栏无法解析，请确认学生身份。",
                    source="identity_parser",
                )
            )
        elif identity.status == StudentIdentityCandidate.STATUS_LOW_CONFIDENCE:
            queue.append(
                RecognitionException(
                    code="IDENTITY_LOW_CONFIDENCE",
                    level=RecognitionException.LEVEL_REVIEW,
                    message=identity.message or "姓名栏识别置信度较低，请确认。",
                    source="identity_parser",
                )
            )

    # -- draft exceptions ----------------------------------------------------
    judgment_map: dict = {}
    if judgments is not None:
        judgment_map = {idx: j for idx, j in enumerate(judgments)}

    for draft in drafts:
        exc = _draft_exception(draft)
        if exc is not None:
            queue.append(exc)

    # -- judgment exceptions -------------------------------------------------
    if judgments is not None:
        for judgment in judgments:
            exc = _judgment_exception(judgment, judgment_threshold)
            if exc is not None:
                queue.append(exc)

    return queue


def _draft_exception(draft: RecognizedAnswerDraft) -> Optional[RecognitionException]:
    """Map a single draft to an exception (if any)."""
    q = draft.question_number
    status = draft.status

    if status == RecognizedAnswerDraft.STATUS_UNCLEAR:
        return RecognitionException(
            code="DRAFT_UNCLEAR",
            level=RecognitionException.LEVEL_REVIEW,
            message=draft.message or f"第 {q} 题识别不清，请确认。",
            student_id=draft.student_id,
            student_name=draft.student_name,
            question_number=q,
            source=draft.source,
            draft=draft,
        )

    if status == RecognizedAnswerDraft.STATUS_INVALID:
        return RecognitionException(
            code="DRAFT_INVALID",
            level=RecognitionException.LEVEL_REVIEW,
            message=draft.message or f"第 {q} 题识别出异常答案，请确认。",
            student_id=draft.student_id,
            student_name=draft.student_name,
            question_number=q,
            source=draft.source,
            draft=draft,
        )

    if status == RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE:
        return RecognitionException(
            code="DRAFT_LOW_CONFIDENCE",
            level=RecognitionException.LEVEL_REVIEW,
            message=draft.message or f"第 {q} 题识别置信度较低，请确认。",
            student_id=draft.student_id,
            student_name=draft.student_name,
            question_number=q,
            source=draft.source,
            draft=draft,
        )

    if status == RecognizedAnswerDraft.STATUS_CONFLICT:
        return RecognitionException(
            code="DRAFT_CONFLICT",
            level=RecognitionException.LEVEL_REVIEW,
            message=draft.message or f"第 {q} 题识别结果存在冲突，请确认。",
            student_id=draft.student_id,
            student_name=draft.student_name,
            question_number=q,
            source=draft.source,
            draft=draft,
        )

    if status == RecognizedAnswerDraft.STATUS_NEEDS_REVIEW:
        return RecognitionException(
            code="DRAFT_NEEDS_REVIEW",
            level=RecognitionException.LEVEL_REVIEW,
            message=draft.message or f"第 {q} 题需要人工复核。",
            student_id=draft.student_id,
            student_name=draft.student_name,
            question_number=q,
            source=draft.source,
            draft=draft,
        )

    return None


def _judgment_exception(
    judgment: QwenJudgmentMock,
    threshold: float,
) -> Optional[RecognitionException]:
    """Check a Qwen judgment for exception conditions."""
    # needs_review verdict
    if judgment.verdict == QwenJudgmentMock.VERDICT_NEEDS_REVIEW:
        return RecognitionException(
            code="QWEN_NEEDS_REVIEW",
            level=RecognitionException.LEVEL_REVIEW,
            message="千问判断为需要复核。",
            source="qwen_judgment",
        )

    # invalid verdict
    if judgment.verdict == QwenJudgmentMock.VERDICT_INVALID:
        return RecognitionException(
            code="QWEN_INVALID",
            level=RecognitionException.LEVEL_REVIEW,
            message="千问判断为无法判定，请人工确认。",
            source="qwen_judgment",
        )

    # low confidence
    if judgment.confidence < threshold:
        return RecognitionException(
            code="QWEN_LOW_CONFIDENCE",
            level=RecognitionException.LEVEL_REVIEW,
            message=f"千问判定置信度较低（{judgment.confidence}），请确认。",
            source="qwen_judgment",
        )

    # empty reason
    if not (judgment.reason or "").strip():
        return RecognitionException(
            code="QWEN_MISSING_REASON",
            level=RecognitionException.LEVEL_WARNING,
            message="千问判定未提供理由。",
            source="qwen_judgment",
        )

    # missing normalised fields
    if not (judgment.normalized_standard or "").strip() or not (
        judgment.normalized_student or ""
    ).strip():
        return RecognitionException(
            code="QWEN_MISSING_NORMALIZATION",
            level=RecognitionException.LEVEL_WARNING,
            message="千问判定缺少标准化结果。",
            source="qwen_judgment",
        )

    return None
