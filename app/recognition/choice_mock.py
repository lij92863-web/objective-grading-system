"""Choice-answer recognition normalisation (mock stage).

Normalises mock Qwen choice-cell outputs into ``RecognizedAnswerDraft``
instances.  No real API calls.
"""

import re
from typing import FrozenSet, Optional

from .models import ChoiceCellOutput, ChoiceRecognitionResult, RecognizedAnswerDraft

_VALID_OPTIONS = set("ABCD")
_OPTION_ONLY_RE = re.compile(r"^[A-D]+$", re.IGNORECASE)
_LOW_CONFIDENCE_THRESHOLD = 0.80


def _normalize_option_string(text: str) -> str:
    """Sort and uppercase an option string, e.g. 'BA' → 'AB'."""
    cleaned = (text or "").strip().upper().replace(" ", "")
    return "".join(sorted(char for char in cleaned if char in _VALID_OPTIONS))


def normalize_choice_recognition(
    cell_output: ChoiceCellOutput,
    question_number: int = 0,
    low_confidence_threshold: float = _LOW_CONFIDENCE_THRESHOLD,
) -> RecognizedAnswerDraft:
    """Convert a mock Qwen choice-cell output into a recognition draft.

    Parameters
    ----------
    cell_output:
        The mock Qwen result with ``answer`` and ``confidence``.
    question_number:
        The question number (1-based).
    low_confidence_threshold:
        Confidence values strictly below this are treated as low-confidence.
    """
    raw_answer = (cell_output.answer or "").strip().upper()
    confidence = cell_output.confidence

    # blank ----------------------------------------------------------------
    if raw_answer in ("", "BLANK"):
        return RecognizedAnswerDraft(
            question_number=question_number,
            question_type="single_choice",
            raw_text="",
            normalized_text="",
            confidence=confidence,
            source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
            status=RecognizedAnswerDraft.STATUS_BLANK,
            message="未作答。",
            needs_review=False,
        )

    # unclear --------------------------------------------------------------
    if raw_answer == "UNCLEAR":
        return RecognizedAnswerDraft(
            question_number=question_number,
            question_type="single_choice",
            raw_text="unclear",
            normalized_text="",
            confidence=confidence,
            source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
            status=RecognizedAnswerDraft.STATUS_UNCLEAR,
            message=f"第 {question_number} 题识别不清，请确认。",
            needs_review=True,
        )

    # invalid (non A-D characters) -----------------------------------------
    if not _OPTION_ONLY_RE.match(raw_answer):
        return RecognizedAnswerDraft(
            question_number=question_number,
            question_type="single_choice",
            raw_text=raw_answer,
            normalized_text="",
            confidence=confidence,
            source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
            status=RecognizedAnswerDraft.STATUS_INVALID,
            message=f"识别出异常选项 {raw_answer}。",
            needs_review=True,
        )

    # valid choice text ----------------------------------------------------
    normalized = _normalize_option_string(raw_answer)
    below_threshold = confidence < low_confidence_threshold

    return RecognizedAnswerDraft(
        question_number=question_number,
        question_type="multiple_choice" if len(normalized) > 1 else "single_choice",
        raw_text=raw_answer,
        normalized_text=normalized,
        confidence=confidence,
        source=RecognizedAnswerDraft.SOURCE_QWEN_MOCK,
        status=RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE
        if below_threshold
        else RecognizedAnswerDraft.STATUS_DRAFT,
        message=f"第 {question_number} 题识别置信度较低，请确认。"
        if below_threshold
        else "",
        needs_review=below_threshold,
    )
