"""Blank-answer recognition normalisation (mock stage).

Normalises mock Qwen blank-answer OCR results into ``RecognizedAnswerDraft``
instances.  Does NOT perform final scoring — that remains with the grading
core.
"""

from .models import MockBlankOutput, RecognizedAnswerDraft

_LOW_CONFIDENCE_THRESHOLD = 0.80


def normalize_blank_recognition(
    mock_output: MockBlankOutput,
    question_number: int = 0,
    low_confidence_threshold: float = _LOW_CONFIDENCE_THRESHOLD,
) -> RecognizedAnswerDraft:
    """Convert a mock Qwen blank-answer OCR result into a recognition draft.

    Parameters
    ----------
    mock_output:
        The mock Qwen OCR result with ``raw_text``, ``latex``, ``confidence``,
        and ``status``.
    question_number:
        The question number (1-based).
    low_confidence_threshold:
        Confidence values strictly below this are treated as low-confidence.
    """
    raw_text = (mock_output.raw_text or "").strip()
    confidence = mock_output.confidence
    status = (mock_output.status or "").strip().lower()
    latex = (mock_output.latex or "").strip()

    # unclear --------------------------------------------------------------
    if status == "unclear" or raw_text.lower() == "unclear":
        return RecognizedAnswerDraft(
            question_number=question_number,
            question_type="blank",
            raw_text="unclear",
            latex=latex,
            confidence=confidence,
            source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
            status=RecognizedAnswerDraft.STATUS_UNCLEAR,
            message=f"第 {question_number} 题识别不清，请确认。",
            needs_review=True,
        )

    # blank ----------------------------------------------------------------
    if status == "blank" or not raw_text:
        return RecognizedAnswerDraft(
            question_number=question_number,
            question_type="blank",
            raw_text="",
            latex="",
            confidence=confidence,
            source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
            status=RecognizedAnswerDraft.STATUS_BLANK,
            message="未作答。",
            needs_review=False,
        )

    # low confidence -------------------------------------------------------
    below_threshold = confidence < low_confidence_threshold
    if below_threshold:
        return RecognizedAnswerDraft(
            question_number=question_number,
            question_type="blank",
            raw_text=raw_text,
            normalized_text=raw_text,
            latex=latex,
            confidence=confidence,
            source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
            status=RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE,
            message=f"第 {question_number} 题填空答案置信度较低，请确认。",
            needs_review=True,
        )

    # normal recognized ----------------------------------------------------
    return RecognizedAnswerDraft(
        question_number=question_number,
        question_type="blank",
        raw_text=raw_text,
        normalized_text=raw_text,
        latex=latex,
        confidence=confidence,
        source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
        status=RecognizedAnswerDraft.STATUS_DRAFT,
        message="",
        needs_review=False,
    )
