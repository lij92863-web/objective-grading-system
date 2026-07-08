"""Mapping layer: QwenParsedResult → existing recognition domain types.

Bridges the adapter-layer ``QwenParsedResult`` to the domain models in
``app.recognition.models`` so the existing pipeline can consume adapter
output without change.
"""

import dataclasses
from typing import Optional

from ..choice_mock import normalize_choice_recognition
from ..blank_mock import normalize_blank_recognition
from ..models import (
    ChoiceCellOutput,
    MockBlankOutput,
    QwenJudgmentMock,
    RecognizedAnswerDraft,
    StudentIdentityCandidate,
)
from ..qwen_judgment_mock import should_auto_accept_qwen_judgment
from .models import (
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
    QwenParsedResult,
)


# ---------------------------------------------------------------------------
# Name field → StudentIdentityCandidate
# ---------------------------------------------------------------------------


def parse_name_field_to_identity_candidate(
    result: QwenParsedResult,
    roster: Optional[dict[str, str]] = None,
) -> StudentIdentityCandidate:
    """Convert a name-field parsed result to a ``StudentIdentityCandidate``.

    Delegates identity parsing to ``parse_student_identity`` from the
    recognition layer so roster validation stays in one place.
    """
    from ..identity_parser import parse_student_identity

    raw_text = str(result.data.get("raw_text", "")).strip()
    confidence = result.confidence
    return parse_student_identity(raw_text, roster=roster, confidence=confidence)


# ---------------------------------------------------------------------------
# Choice cell → RecognizedAnswerDraft
# ---------------------------------------------------------------------------


def parse_choice_response_to_draft(
    result: QwenParsedResult,
    question_number: int = 0,
) -> RecognizedAnswerDraft:
    """Convert a choice-cell parsed result to a ``RecognizedAnswerDraft``."""
    cell = ChoiceCellOutput(
        answer=str(result.data.get("answer", "")),
        confidence=result.confidence,
    )
    return normalize_choice_recognition(cell, question_number=question_number)


# ---------------------------------------------------------------------------
# Blank answer → RecognizedAnswerDraft
# ---------------------------------------------------------------------------


def parse_blank_response_to_draft(
    result: QwenParsedResult,
    question_number: int = 0,
) -> RecognizedAnswerDraft:
    """Convert a blank-answer parsed result to a ``RecognizedAnswerDraft``."""
    mock = MockBlankOutput(
        raw_text=str(result.data.get("raw_text", "")),
        latex=str(result.data.get("latex", "")),
        confidence=result.confidence,
        status=str(result.data.get("status", "recognized")),
    )
    return normalize_blank_recognition(mock, question_number=question_number)


# ---------------------------------------------------------------------------
# Complex judgment → QwenJudgmentMock
# ---------------------------------------------------------------------------


def parse_complex_judgment_response(
    result: QwenParsedResult,
) -> QwenJudgmentMock:
    """Convert a complex-blank judgment parsed result to a ``QwenJudgmentMock``."""
    verdict = str(result.data.get("verdict", "needs_review")).strip().lower()
    if verdict not in QwenJudgmentMock.VALID_VERDICTS:
        verdict = QwenJudgmentMock.VERDICT_NEEDS_REVIEW

    return QwenJudgmentMock(
        verdict=verdict,
        confidence=result.confidence,
        reason=str(result.data.get("reason", "")),
        normalized_standard=str(result.data.get("normalized_standard", "")),
        normalized_student=str(result.data.get("normalized_student", "")),
        equivalence_type=str(result.data.get("equivalence_type", "unknown")),
        requires_review=bool(result.data.get("requires_review", True)),
    )


# ---------------------------------------------------------------------------
# Dispatchers (convenience)
# ---------------------------------------------------------------------------

_MAPPERS = {
    PROMPT_TYPE_NAME_FIELD: parse_name_field_to_identity_candidate,
    PROMPT_TYPE_CHOICE_CELL: parse_choice_response_to_draft,
    PROMPT_TYPE_BLANK_ANSWER: parse_blank_response_to_draft,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT: parse_complex_judgment_response,
}
