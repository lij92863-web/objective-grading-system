"""Fake Qwen client — returns preset JSON without real API calls.

Injects known-good and known-bad responses for testing the parser,
validator, and mapping layers.  No network I/O.
"""

import json
from typing import Optional

from .client import QwenClient
from .models import (
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
    QwenRawResponse,
    QwenRequest,
)

# ---------------------------------------------------------------------------
# Preset valid responses
# ---------------------------------------------------------------------------

_PRESET_NAME_FIELD_RESPONSE = {
    "raw_text": "1李明",
    "confidence": 0.98,
}

_PRESET_CHOICE_CELL_RESPONSE = {
    "answer": "AB",
    "confidence": 0.96,
}

_PRESET_BLANK_ANSWER_RESPONSE = {
    "raw_text": "1/2",
    "latex": "\\frac{1}{2}",
    "confidence": 0.95,
    "status": "recognized",
}

_PRESET_COMPLEX_JUDGMENT_RESPONSE = {
    "verdict": "correct",
    "confidence": 0.96,
    "reason": "学生答案与标准答案表示同一解集。",
    "normalized_standard": "x > 1",
    "normalized_student": "x > 1",
    "equivalence_type": "same_solution_set",
    "requires_review": False,
}

# ---------------------------------------------------------------------------
# Injectable error responses (keyed by error type)
# ---------------------------------------------------------------------------

_INJECTED_ERRORS: dict[str, str] = {
    "invalid_json": "{not json",
    "missing_field": '{"confidence": 0.9}',
    "invalid_verdict": '{"verdict":"maybe","confidence":0.9,"reason":"?","normalized_standard":"x","normalized_student":"x","requires_review":false}',
    "invalid_confidence": '{"verdict":"correct","confidence":1.5,"reason":"ok","normalized_standard":"x","normalized_student":"x","requires_review":false}',
    "empty_reason": '{"verdict":"correct","confidence":0.96,"reason":"","normalized_standard":"x","normalized_student":"x","requires_review":false}',
    "needs_review_true": '{"verdict":"needs_review","confidence":0.80,"reason":"uncertain","normalized_standard":"x","normalized_student":"y","requires_review":true}',
}

# Map prompt_type -> default preset key
_DEFAULT_PRESETS = {
    PROMPT_TYPE_NAME_FIELD: "name_field",
    PROMPT_TYPE_CHOICE_CELL: "choice_cell",
    PROMPT_TYPE_BLANK_ANSWER: "blank_answer",
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT: "complex_judgment",
}

_PRESET_DATA = {
    "name_field": _PRESET_NAME_FIELD_RESPONSE,
    "choice_cell": _PRESET_CHOICE_CELL_RESPONSE,
    "blank_answer": _PRESET_BLANK_ANSWER_RESPONSE,
    "complex_judgment": _PRESET_COMPLEX_JUDGMENT_RESPONSE,
}


class FakeQwenClient(QwenClient):
    """Fake Qwen client for testing and development.

    Returns preset valid JSON by default.  Call ``inject_error()`` to
    override the next response with a known error shape.
    """

    def __init__(self) -> None:
        self._error_injection: Optional[str] = None
        self._custom_payload: Optional[dict] = None

    # -- injection API ---------------------------------------------------------

    def inject_error(self, error_key: str) -> None:
        """Cause the **next single call** to return a known error response.

        One-shot: the second call reverts to default presets.  Use
        multiple ``inject_error`` calls in sequence if you need several
        consecutive error responses.

        Valid keys: ``invalid_json``, ``missing_field``, ``invalid_verdict``,
        ``invalid_confidence``, ``empty_reason``, ``needs_review_true``.
        """
        self._error_injection = error_key

    def inject_custom_payload(self, payload: dict) -> None:
        """Cause the **next single call** to return *payload*.

        One-shot: the second call reverts to default presets.
        """
        self._custom_payload = payload

    def clear_injection(self) -> None:
        """Reset injections — next call returns default preset."""
        self._error_injection = None
        self._custom_payload = None

    # -- QwenClient implementation --------------------------------------------

    def _consume_injections(self) -> tuple[Optional[str], Optional[dict]]:
        """Pop and return current injections, resetting them to None.

        One-shot semantics: each injection applies to exactly one call.
        """
        error_key = self._error_injection
        payload = self._custom_payload
        self._error_injection = None
        self._custom_payload = None
        return error_key, payload

    def _make_response(self, prompt_type: str, request: QwenRequest) -> QwenRawResponse:
        """Build a response — one-shot injection, then preset."""
        error_key, payload = self._consume_injections()

        if error_key is not None:
            return self._build_error(request, error_key)
        if payload is not None:
            raw_text = json.dumps(payload, ensure_ascii=False)
            return QwenRawResponse(
                request_id=request.request_id,
                raw_text=raw_text,
                parsed_json=payload,
                model="fake-qwen",
            )
        preset = _PRESET_DATA.get(prompt_type, _PRESET_CHOICE_CELL_RESPONSE)
        raw_text = json.dumps(preset, ensure_ascii=False)
        return QwenRawResponse(
            request_id=request.request_id,
            raw_text=raw_text,
            parsed_json=preset,
            model="fake-qwen",
        )

    def _build_error(self, request: QwenRequest, error_key: str) -> QwenRawResponse:
        text = _INJECTED_ERRORS.get(error_key, "{}")
        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass
        return QwenRawResponse(
            request_id=request.request_id,
            raw_text=text,
            parsed_json=parsed,
        )

    def recognize_name_field(self, request: QwenRequest) -> QwenRawResponse:
        return self._make_response("name_field", request)

    def recognize_choice_cell(self, request: QwenRequest) -> QwenRawResponse:
        return self._make_response("choice_cell", request)

    def recognize_blank_answer(self, request: QwenRequest) -> QwenRawResponse:
        return self._make_response("blank_answer", request)

    def judge_complex_blank(self, request: QwenRequest) -> QwenRawResponse:
        return self._make_response("complex_judgment", request)
