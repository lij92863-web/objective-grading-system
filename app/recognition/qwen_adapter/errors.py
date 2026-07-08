"""Qwen adapter error codes — safe, structured, no raw data leakage."""


class QwenAdapterErrorCode:
    """Machine-readable error codes for the Qwen adapter layer.

    Do NOT include API keys, base64 image data, or raw responses in error
    messages.
    """

    INVALID_JSON = "invalid_json"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_VERDICT = "invalid_verdict"
    INVALID_CONFIDENCE = "invalid_confidence"
    API_DISABLED = "api_disabled"
    MISSING_API_KEY = "missing_api_key"
    MISSING_API_BASE = "missing_api_base"
    MISSING_MODEL = "missing_model"
    IMAGE_NOT_FOUND = "image_not_found"
    HTTP_ERROR = "http_error"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    UNSAFE_RESPONSE = "unsafe_response"
    UNSUPPORTED_PROMPT_TYPE = "unsupported_prompt_type"


class QwenAdapterError(Exception):
    """Structured error raised by the Qwen adapter layer.

    Parameters
    ----------
    code:
        One of ``QwenAdapterErrorCode`` constants.
    message:
        Human-readable description (must NOT contain raw API keys, base64
        image data, or full response bodies).
    detail:
        Optional structured detail dict.
    """

    def __init__(self, code: str, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail or {}

    def __repr__(self) -> str:
        return f"QwenAdapterError(code={self.code!r}, message={self.message!r})"
