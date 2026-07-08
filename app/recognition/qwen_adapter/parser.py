"""Qwen response parser — JSON parse + validation → QwenParsedResult."""

import json
from typing import Optional

from .errors import QwenAdapterError, QwenAdapterErrorCode
from .models import QwenParsedResult, QwenRawResponse
from .validators import get_validator


def parse_qwen_response(
    response: QwenRawResponse,
    prompt_type: str,
    request_id: str = "",
) -> QwenParsedResult:
    """Parse and validate a raw Qwen response.

    Parameters
    ----------
    response:
        The raw response from the client.
    prompt_type:
        One of ``name_field``, ``choice_cell``, ``blank_answer``,
        ``complex_blank_judgment``.
    request_id:
        For tracing.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Parse JSON -----------------------------------------------------------
    data: dict = {}
    if response.parsed_json is not None:
        data = response.parsed_json
    else:
        try:
            data = json.loads(response.raw_text or "{}")
        except json.JSONDecodeError:
            return QwenParsedResult(
                prompt_type=prompt_type,
                status="error",
                errors=[QwenAdapterErrorCode.INVALID_JSON],
                warnings=warnings,
            )
    if not isinstance(data, dict):
        return QwenParsedResult(
            prompt_type=prompt_type,
            status="error",
            errors=[QwenAdapterErrorCode.INVALID_JSON],
        )

    # 2. Validate -------------------------------------------------------------
    validator = get_validator(prompt_type)
    if validator is None:
        return QwenParsedResult(
            prompt_type=prompt_type,
            status="error",
            errors=[QwenAdapterErrorCode.UNSUPPORTED_PROMPT_TYPE],
        )

    validation_errors = validator(data)
    errors.extend(validation_errors)

    # 3. Extract confidence ---------------------------------------------------
    confidence = 0.0
    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        pass

    return QwenParsedResult(
        prompt_type=prompt_type,
        status="error" if errors else "ok",
        data=data,
        confidence=confidence,
        errors=errors,
        warnings=warnings,
    )
