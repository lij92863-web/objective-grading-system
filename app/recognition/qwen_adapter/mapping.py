"""Mapping layer: QwenParsedResult → existing recognition domain types.

Bridges the adapter-layer ``QwenParsedResult`` to the domain models in
``app.recognition.models`` so the existing pipeline can consume adapter
output without change.

Every mapping function enforces a hard gate: if ``result.status != "ok"``
or ``result.errors`` is non-empty the function raises ``QwenAdapterError``
with code ``unsafe_response``.  Error results must never be silently
converted into drafts.
"""

from typing import Optional

from .errors import QwenAdapterError, QwenAdapterErrorCode
from .models import QwenParsedResult

# Import domain models at function-call time to avoid circular imports
# with the parent recognition package at module level.


def _guard(result: QwenParsedResult, label: str = "") -> None:
    """Raise ``QwenAdapterError`` if *result* is not safe to map."""
    if result.status != "ok" or result.errors:
        detail = {
            "status": result.status,
            "errors": result.errors,
            "function": label,
        }
        raise QwenAdapterError(
            QwenAdapterErrorCode.UNSAFE_RESPONSE,
            f"Cannot map a failed/error result. status={result.status!r}, errors={result.errors}",
            detail,
        )


def _safe_bool(value: object, default: bool = True) -> bool:
    """Extract a strict bool from *value*.

    ``bool("false")`` would be ``True`` in Python — we forbid that.
    Returns *default* only when *value* is ``None``.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise QwenAdapterError(
        QwenAdapterErrorCode.INVALID_VERDICT,
        f"requires_review must be a bool, got {type(value).__name__}: {value!r}",
    )


# ---------------------------------------------------------------------------
# Name field → StudentIdentityCandidate
# ---------------------------------------------------------------------------


def parse_name_field_to_identity_candidate(
    result: QwenParsedResult,
    roster: Optional[dict[str, str]] = None,
) -> "StudentIdentityCandidate":
    """Convert a name-field parsed result to a ``StudentIdentityCandidate``."""
    _guard(result, "parse_name_field_to_identity_candidate")

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
) -> "RecognizedAnswerDraft":
    """Convert a choice-cell parsed result to a ``RecognizedAnswerDraft``."""
    _guard(result, "parse_choice_response_to_draft")

    from ..choice_mock import normalize_choice_recognition
    from ..models import ChoiceCellOutput

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
) -> "RecognizedAnswerDraft":
    """Convert a blank-answer parsed result to a ``RecognizedAnswerDraft``."""
    _guard(result, "parse_blank_response_to_draft")

    from ..blank_mock import normalize_blank_recognition
    from ..models import MockBlankOutput

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
) -> "QwenJudgmentMock":
    """Convert a complex-blank judgment parsed result to a ``QwenJudgmentMock``."""
    _guard(result, "parse_complex_judgment_response")

    from ..models import QwenJudgmentMock

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
        requires_review=_safe_bool(result.data.get("requires_review"), default=True),
    )


# ---------------------------------------------------------------------------
# Dispatchers (convenience)
# ---------------------------------------------------------------------------

from .models import (  # noqa: E402
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
)

_MAPPERS = {
    PROMPT_TYPE_NAME_FIELD: parse_name_field_to_identity_candidate,
    PROMPT_TYPE_CHOICE_CELL: parse_choice_response_to_draft,
    PROMPT_TYPE_BLANK_ANSWER: parse_blank_response_to_draft,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT: parse_complex_judgment_response,
}
