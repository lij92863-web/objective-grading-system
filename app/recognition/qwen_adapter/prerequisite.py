"""R41: Controlled Qwen prerequisite detector."""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

SUPPORTED_MIME_EXT = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class PrerequisiteReport:
    allow_real_api: bool = False
    image_path: str = ""
    api_key_env: str = ""
    checks_passed: bool = False
    errors: List[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def check_prerequisites(allow_real_api: bool = False, image_path: str = "",
                        api_key_env: str = "QWEN_API_KEY",
                        save_raw_response: bool = False,
                        emit_base64: bool = False) -> PrerequisiteReport:
    errors = []
    if not allow_real_api:
        errors.append("REAL_API_NOT_ALLOWED")
    if not image_path:
        errors.append("IMAGE_PATH_MISSING")
    else:
        p = Path(image_path)
        if not p.exists(): errors.append("IMAGE_NOT_FOUND")
        elif p.stat().st_size == 0: errors.append("IMAGE_EMPTY")
        if p.suffix.lower() not in SUPPORTED_MIME_EXT: errors.append("IMAGE_UNSUPPORTED_MIME")
    if not api_key_env:
        errors.append("API_KEY_ENV_MISSING")
    elif not os.environ.get(api_key_env):
        errors.append("API_KEY_NOT_IN_ENVIRONMENT")
    if save_raw_response:
        errors.append("SAVE_RAW_RESPONSE_FORBIDDEN")
    if emit_base64:
        errors.append("EMIT_BASE64_FORBIDDEN")
    checks_passed = len(errors) == 0
    summary = {"allow_real_api": allow_real_api, "image_basename": Path(image_path).name if image_path else "",
               "api_key_env": api_key_env, "api_key_present": bool(os.environ.get(api_key_env))}
    return PrerequisiteReport(allow_real_api=allow_real_api, image_path=image_path,
                               api_key_env=api_key_env, checks_passed=checks_passed,
                               errors=errors, summary=summary)
