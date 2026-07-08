"""Qwen response validators.

Each validator checks a parsed JSON payload and returns a list of error
codes (empty list = valid).  These are pure functions — no side effects.
"""

from typing import List, Optional

from .errors import QwenAdapterErrorCode

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_confidence(data: dict, errors: List[str]) -> None:
    confidence = data.get("confidence")
    if confidence is None:
        return
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        errors.append(QwenAdapterErrorCode.INVALID_CONFIDENCE)
        return
    if value < 0.0 or value > 1.0:
        errors.append(QwenAdapterErrorCode.INVALID_CONFIDENCE)


def _check_requires_review(data: dict, errors: List[str]) -> None:
    rrv = data.get("requires_review")
    if rrv is not None and not isinstance(rrv, bool):
        errors.append(QwenAdapterErrorCode.INVALID_VERDICT)


# ---------------------------------------------------------------------------
# Per-type validators
# ---------------------------------------------------------------------------


def validate_name_field_response(data: dict) -> List[str]:
    """Validate a name-field recognition payload."""
    errors: List[str] = []
    raw_text = str(data.get("raw_text", "")).strip()
    if not raw_text:
        errors.append(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD)
    _check_confidence(data, errors)
    return errors


def validate_choice_cell_response(data: dict) -> List[str]:
    """Validate a choice-cell recognition payload."""
    errors: List[str] = []
    answer = str(data.get("answer", "")).strip().upper()
    if not answer:
        errors.append(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD)
    else:
        valid_answers = {"A", "B", "C", "D", "AB", "AC", "AD", "BC", "BD", "CD",
                         "ABC", "ABD", "ACD", "BCD", "ABCD", "BLANK", "UNCLEAR", "INVALID"}
        if answer not in valid_answers:
            errors.append(QwenAdapterErrorCode.INVALID_VERDICT)
    _check_confidence(data, errors)
    return errors


def validate_blank_answer_response(data: dict) -> List[str]:
    """Validate a blank-answer OCR payload."""
    errors: List[str] = []
    raw_text = str(data.get("raw_text", "")).strip()
    status = str(data.get("status", "")).strip().lower()
    if not raw_text and not status:
        errors.append(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD)
    if status and status not in ("recognized", "blank", "unclear"):
        errors.append(QwenAdapterErrorCode.INVALID_VERDICT)
    _check_confidence(data, errors)
    return errors


def validate_complex_blank_judgment_response(data: dict) -> List[str]:
    """Validate a complex-blank judgment payload."""
    errors: List[str] = []
    verdict = str(data.get("verdict", "")).strip().lower()
    valid_verdicts = {"correct", "wrong", "partial", "needs_review", "invalid"}
    if not verdict:
        errors.append(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD)
    elif verdict not in valid_verdicts:
        errors.append(QwenAdapterErrorCode.INVALID_VERDICT)

    _check_confidence(data, errors)

    # reason required unless verdict == invalid
    reason = str(data.get("reason", "")).strip()
    if not reason and verdict != "invalid":
        errors.append(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD)

    # normalized fields required for correct/wrong/partial
    if verdict in ("correct", "wrong", "partial"):
        ns = str(data.get("normalized_standard", "")).strip()
        nu = str(data.get("normalized_student", "")).strip()
        if not ns or not nu:
            errors.append(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD)

    _check_requires_review(data, errors)
    return errors


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

VALIDATORS_BY_PROMPT_TYPE = {
    "name_field": validate_name_field_response,
    "choice_cell": validate_choice_cell_response,
    "blank_answer": validate_blank_answer_response,
    "complex_blank_judgment": validate_complex_blank_judgment_response,
}


def get_validator(prompt_type: str):
    """Return the validator function for *prompt_type*, or ``None``."""
    return VALIDATORS_BY_PROMPT_TYPE.get(prompt_type)
