"""Single Qwen Sanitizer — strips raw headers, API keys, base64, raw image data.

Takes a raw/fake Qwen response payload and produces a safe
SingleQwenSanitizedOutput.  Malformed responses produce engine_error status.
"""

import json
from typing import Any, Dict, List, Optional

from .single_sanitized_output import (
    SanitizedCandidate,
    SanitizedIdentityCandidate,
    SingleQwenSanitizedOutput,
)


FORBIDDEN_KEYS = {
    "api_key", "authorization", "bearer", "sk-",
    "data:image", "base64", "raw_http_response",
    "x-api-key", "access_token",
}

FORBIDDEN_VALUE_PATTERNS = ["sk-", "Bearer ", "data:image", "base64,"]


def sanitize_single_qwen_response(
    raw_payload: dict,
    request_id: str = "",
    image_sha256: str = "",
    engine_name: str = "qwen",
    real_api_called: bool = False,
) -> SingleQwenSanitizedOutput:
    """Sanitize a raw Qwen response into a safe structured output.

    Parameters
    ----------
    raw_payload: The raw response dict (fake or real-like).
    request_id: Request identifier for tracing.
    image_sha256: Image hash prefix (safe to include).
    engine_name: Engine identifier.
    real_api_called: Whether a real API was actually called.
    """
    warnings: List[str] = []
    exception_codes: List[str] = []

    # 1. Strip forbidden top-level keys
    cleaned = {}
    for key, value in raw_payload.items():
        key_lower = key.lower()
        if any(forbidden in key_lower for forbidden in FORBIDDEN_KEYS):
            warnings.append(f"STRIPPED_FORBIDDEN_KEY:{key}")
            continue
        if isinstance(value, str):
            if any(pattern in value for pattern in FORBIDDEN_VALUE_PATTERNS):
                warnings.append(f"STRIPPED_FORBIDDEN_VALUE_IN_KEY:{key}")
                continue
        cleaned[key] = value

    # 2. Determine engine status
    engine_status = "ok"
    if not cleaned:
        engine_status = "engine_error"
        exception_codes.append("EMPTY_RESPONSE_AFTER_SANITIZATION")

    # 3. Parse candidates
    candidates = []
    identity_candidate = None

    items = cleaned.get("items", [])
    if not isinstance(items, list):
        engine_status = "engine_error"
        exception_codes.append("MALFORMED_ITEMS_NOT_LIST")
        items = []

    for item in items:
        if not isinstance(item, dict):
            exception_codes.append("MALFORMED_ITEM_NOT_DICT")
            continue
        candidate = SanitizedCandidate(
            question_id=str(item.get("question_id", "")),
            question_type=str(item.get("question_type", "")),
            answer=str(item.get("answer", "")),
            raw_text=str(item.get("raw_text", "")),
            confidence=_safe_float(item.get("confidence"), 0.0),
            needs_review=bool(item.get("needs_review", False)),
            invalid_option=bool(item.get("invalid_option", False)),
            warnings=list(item.get("warnings", []) if isinstance(item.get("warnings"), list) else []),
        )
        candidates.append(candidate)

    # Identity candidate
    identity_raw = cleaned.get("identity_candidate")
    if isinstance(identity_raw, dict):
        identity_candidate = SanitizedIdentityCandidate(
            raw_text=str(identity_raw.get("raw_text", "")),
            student_number=str(identity_raw.get("student_number", "")),
            student_name=str(identity_raw.get("student_name", "")),
            confidence=_safe_float(identity_raw.get("confidence"), 0.0),
            needs_review=True,  # Always needs review
        )

    return SingleQwenSanitizedOutput(
        request_id=request_id,
        engine_name=engine_name,
        engine_status=engine_status,
        real_api_called=real_api_called,
        raw_response_saved=False,
        base64_emitted=False,
        image_sha256=image_sha256[:12] if image_sha256 else "",
        candidate_count=len(candidates),
        candidates=candidates,
        identity_candidate=identity_candidate,
        warnings=warnings,
        exception_codes=exception_codes,
    )


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        v = float(value)
        if v < 0.0 or v > 1.0:
            return max(0.0, min(1.0, v))
        return v
    except (TypeError, ValueError):
        return default
