"""Single Qwen Trial Config — default fail-closed, no real API.

All fields default to safe values. allow_real_api defaults to False.
save_raw_response and emit_base64 must always be False.
api_key_env stores env var NAME only, never the key value.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


FORBIDDEN_CONFIG_VALUES = {"sk-", "Bearer ", "data:image", "base64,"}


@dataclass
class SingleQwenTrialConfig:
    config_version: int = 1
    manifest_path: str = ""
    roi_path: str = ""
    prompt_version: str = "v2"
    engine_name: str = "qwen"
    check_only: bool = True
    allow_real_api: bool = False
    api_key_env: str = ""
    output_dir: str = "data/tmp"
    save_raw_response: bool = False
    emit_base64: bool = False
    max_calls: int = 1
    require_anonymous: bool = True
    require_manual_roi: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SingleQwenTrialConfig":
        return cls(**{f: data.get(f, getattr(cls(), f))
                      for f in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_single_qwen_trial_config(config: SingleQwenTrialConfig) -> dict:
    blockers: List[str] = []
    warnings: List[str] = []

    # 1. Default fail-closed
    if not config.check_only:
        warnings.append("CHECK_ONLY_OFF")
    if config.allow_real_api:
        # Not an error, but unusual for this stage
        warnings.append("ALLOW_REAL_API_EXPLICITLY_TRUE")

    # 2. Forbidden flags
    if config.save_raw_response:
        blockers.append("SAVE_RAW_RESPONSE_MUST_BE_FALSE")
    if config.emit_base64:
        blockers.append("EMIT_BASE64_MUST_BE_FALSE")

    # 3. api_key_env must be a name, not a value
    if config.api_key_env:
        lowered = config.api_key_env.lower()
        for forbidden in FORBIDDEN_CONFIG_VALUES:
            if forbidden.lower() in lowered:
                blockers.append(f"API_KEY_ENV_CONTAINS_SUSPICIOUS_VALUE")
                break
        # Looks like a real key value (too long for env var name)
        if len(config.api_key_env) > 50:
            blockers.append("API_KEY_ENV_LOOKS_LIKE_VALUE_NOT_NAME")

    # 4. max_calls bounds
    if config.max_calls < 0:
        blockers.append("MAX_CALLS_NEGATIVE")
    if config.max_calls > 1:
        blockers.append("MAX_CALLS_EXCEEDS_ONE")

    # 5. require_anonymous and require_manual_roi
    if not config.require_anonymous:
        blockers.append("REQUIRE_ANONYMOUS_MUST_BE_TRUE")
    if not config.require_manual_roi:
        blockers.append("REQUIRE_MANUAL_ROI_MUST_BE_TRUE")

    # 6. manifest/roi paths should be non-empty for real use
    if not config.manifest_path:
        warnings.append("MISSING_MANIFEST_PATH")
    if not config.roi_path:
        warnings.append("MISSING_ROI_PATH")

    # 7. output_dir
    if config.output_dir and "data/reports" in config.output_dir:
        blockers.append("OUTPUT_DIR_MUST_NOT_BE_DATA_REPORTS")

    return {
        "valid": not blockers,
        "warnings": warnings,
        "blockers": blockers,
        "config_summary": safe_config_summary(config),
    }


def safe_config_summary(config: SingleQwenTrialConfig) -> dict:
    return {
        "config_version": config.config_version,
        "manifest_path": Path(config.manifest_path).name if config.manifest_path else "",
        "roi_path": Path(config.roi_path).name if config.roi_path else "",
        "prompt_version": config.prompt_version,
        "engine_name": config.engine_name,
        "check_only": config.check_only,
        "allow_real_api": config.allow_real_api,
        "api_key_env_present": bool(config.api_key_env),
        "output_dir": config.output_dir,
        "save_raw_response": config.save_raw_response,
        "emit_base64": config.emit_base64,
        "max_calls": config.max_calls,
        "require_anonymous": config.require_anonymous,
        "require_manual_roi": config.require_manual_roi,
    }


def load_single_qwen_trial_config(path: str | Path) -> SingleQwenTrialConfig:
    return SingleQwenTrialConfig.from_dict(
        json.loads(Path(path).read_text(encoding="utf-8")))
