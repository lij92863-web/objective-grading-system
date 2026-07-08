"""Real Qwen client — controlled by environment variables.

**Default: disabled.**  Set ``QWEN_API_ENABLED=true`` plus
``QWEN_API_KEY`` and ``QWEN_API_BASE`` to enable real API calls.

Never writes API keys to code, logs, or error messages.
"""

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from .client import QwenClient
from .errors import QwenAdapterError, QwenAdapterErrorCode
from .models import QwenRawResponse, QwenRequest
from .prompt_builder import build_prompt


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() == "true"


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise QwenAdapterError(
            QwenAdapterErrorCode.MISSING_API_KEY
            if "KEY" in name.upper()
            else QwenAdapterErrorCode.MISSING_API_BASE
            if "BASE" in name.upper()
            else QwenAdapterErrorCode.MISSING_MODEL,
            f"Environment variable {name} is not set.",
        )
    return value


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------


def _encode_image(image_path: str) -> str:
    """Read *image_path* and return a base64 data-URL string.

    Raises ``QwenAdapterError(IMAGE_NOT_FOUND)`` if the file is missing.
    Never logs the base64 content.
    """
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        raise QwenAdapterError(
            QwenAdapterErrorCode.IMAGE_NOT_FOUND,
            f"Image not found: {image_path}",
        )
    mime = "image/jpeg"
    suffix = path.suffix.lower()
    if suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"
    raw = path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _safe_image_ref(request: QwenRequest) -> str:
    """Return a safe (non-base64) reference to the request image."""
    if request.image is None:
        return "<no image>"
    if request.image.image_path:
        return f"image_path={request.image.image_path}"
    if request.image.image_base64:
        return "<base64 omitted>"
    return "<no image data>"


# ---------------------------------------------------------------------------
# RealQwenClient
# ---------------------------------------------------------------------------


class RealQwenClient(QwenClient):
    """Real Qwen API client — gated behind environment variables.

    Parameters
    ----------
    api_key:
        Optional override for ``QWEN_API_KEY``.  Still subject to the
        ``QWEN_API_ENABLED`` gate.
    api_base:
        Optional override for ``QWEN_API_BASE``.
    model:
        Optional override for ``QWEN_MODEL``.
    timeout:
        Seconds before HTTP timeout (default 30).
    enabled:
        Optional override for the enabled check.  If ``False`` the client
        is always disabled regardless of environment.
    """

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "",
        model: str = "",
        timeout: int = 30,
        enabled: Optional[bool] = None,
    ) -> None:
        self._api_key = api_key
        self._api_base = api_base
        self._model = model
        self._timeout = timeout
        self._enabled_override = enabled

    # -- gate checks ------------------------------------------------------------

    def _is_enabled(self) -> bool:
        if self._enabled_override is not None:
            return self._enabled_override
        return _env_flag("QWEN_API_ENABLED")

    def _check_config(self) -> tuple[str, str, str]:
        """Verify configuration and return (api_key, api_base, model).

        Raises ``QwenAdapterError`` if disabled or misconfigured.
        """
        if not self._is_enabled():
            raise QwenAdapterError(
                QwenAdapterErrorCode.API_DISABLED,
                "Qwen API is not enabled. "
                "Set QWEN_API_ENABLED=true to enable real API calls.",
            )
        api_key = self._api_key or _require_env("QWEN_API_KEY")
        api_base = self._api_base or _require_env("QWEN_API_BASE")
        model = self._model or _require_env("QWEN_MODEL")
        return api_key, api_base, model

    # -- image resolution -------------------------------------------------------

    def _resolve_image(self, request: QwenRequest) -> str:
        """Return a base64 data URL for the request image.

        Prefers ``image_base64`` on the input (if already provided),
        otherwise reads from ``image_path``.
        """
        if request.image is None:
            raise QwenAdapterError(
                QwenAdapterErrorCode.IMAGE_NOT_FOUND,
                "No image provided in request.",
            )
        if request.image.image_base64:
            return request.image.image_base64
        if request.image.image_path:
            return _encode_image(request.image.image_path)
        raise QwenAdapterError(
            QwenAdapterErrorCode.IMAGE_NOT_FOUND,
            "Image has neither path nor base64 data.",
        )

    # -- HTTP call --------------------------------------------------------------

    def _call_api(
        self,
        request: QwenRequest,
        api_key: str,
        api_base: str,
        model: str,
    ) -> QwenRawResponse:
        prompt = build_prompt(request)
        image_url = self._resolve_image(request)

        body = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
        }
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

        url = api_base.rstrip("/") + "/chat/completions"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw_text = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise QwenAdapterError(
                QwenAdapterErrorCode.HTTP_ERROR,
                f"HTTP {exc.code} from Qwen API: {exc.reason}",
                {"status_code": exc.code},
            ) from exc
        except OSError as exc:
            raise QwenAdapterError(
                QwenAdapterErrorCode.TIMEOUT,
                f"Qwen API request timed out or failed: {exc}",
            ) from exc

        # Parse the OpenAI-compatible response to extract the assistant text.
        parsed_json: Optional[dict] = None
        try:
            outer = json.loads(raw_text)
            choice = outer.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            parsed_json = json.loads(content)
        except (json.JSONDecodeError, IndexError, KeyError, TypeError):
            pass

        return QwenRawResponse(
            request_id=request.request_id,
            raw_text=raw_text,
            parsed_json=parsed_json,
            model=model,
        )

    # -- QwenClient interface ---------------------------------------------------

    def recognize_name_field(self, request: QwenRequest) -> QwenRawResponse:
        api_key, api_base, model = self._check_config()
        return self._call_api(request, api_key, api_base, model)

    def recognize_choice_cell(self, request: QwenRequest) -> QwenRawResponse:
        api_key, api_base, model = self._check_config()
        return self._call_api(request, api_key, api_base, model)

    def recognize_blank_answer(self, request: QwenRequest) -> QwenRawResponse:
        api_key, api_base, model = self._check_config()
        return self._call_api(request, api_key, api_base, model)

    def judge_complex_blank(self, request: QwenRequest) -> QwenRawResponse:
        api_key, api_base, model = self._check_config()
        return self._call_api(request, api_key, api_base, model)
