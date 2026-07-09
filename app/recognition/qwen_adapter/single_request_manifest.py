"""Single Qwen Request Manifest — metadata envelope for a single-image Qwen call.

Tracks what WILL happen before a call is made.  Default fail-closed.
Never contains API keys, base64, or full local image paths.
"""

import json
import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


FORBIDDEN_MANIFEST_KEYS = {"api_key", "base64", "image_base64", "raw_response", "authorization"}


@dataclass
class SingleQwenRequestManifest:
    request_id: str = ""
    request_version: int = 1
    image_id: str = ""
    image_sha256: str = ""
    manifest_valid: bool = False
    roi_valid: bool = False
    prompt_version: str = "v2"
    engine_name: str = "qwen"
    real_api_allowed: bool = False
    check_only: bool = True
    raw_response_saved: bool = False
    base64_emitted: bool = False
    api_key_present: bool = False
    output_policy: str = "data/tmp only"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SingleQwenRequestManifest":
        unknown_forbidden = sorted(FORBIDDEN_MANIFEST_KEYS & set(data))
        if unknown_forbidden:
            raise ValueError(f"manifest contains forbidden fields: {unknown_forbidden}")
        return cls(**{f: data.get(f, getattr(cls(), f))
                      for f in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_request_manifest(
    single_manifest: Any,
    roi_file: Any,
    check_only: bool = True,
    api_key_env: str = "",
) -> SingleQwenRequestManifest:
    """Build a request manifest from single-image manifest + ROI.

    Never reads .env. api_key_env is just the var name.
    """
    import uuid

    request_id = uuid.uuid4().hex[:12]

    # Validate inputs
    from app.recognition.single_image_manifest import validate_single_image_manifest
    from app.recognition.manual_roi_schema import validate_manual_roi_file

    manifest_result = validate_single_image_manifest(single_manifest)
    roi_result = validate_manual_roi_file(roi_file)

    # Image sha256
    image_sha256 = ""
    if hasattr(single_manifest, 'image_sha256') and single_manifest.image_sha256:
        image_sha256 = single_manifest.image_sha256

    # Check api_key_env presence (don't read .env, just check os.environ)
    api_key_present = False
    if api_key_env:
        import os
        api_key_present = bool(os.environ.get(api_key_env, "").strip())

    image_id = ""
    if hasattr(single_manifest, 'image_id'):
        image_id = single_manifest.image_id

    return SingleQwenRequestManifest(
        request_id=request_id,
        image_id=image_id,
        image_sha256=image_sha256[:12] if image_sha256 else "",
        manifest_valid=manifest_result.get("valid", False),
        roi_valid=roi_result.get("valid", False),
        check_only=check_only,
        real_api_allowed=False,
        raw_response_saved=False,
        base64_emitted=False,
        api_key_present=api_key_present,
    )


def validate_request_manifest(manifest: SingleQwenRequestManifest) -> dict:
    """Validate a request manifest for safety."""
    blockers: List[str] = []
    warnings: List[str] = []

    if manifest.raw_response_saved:
        blockers.append("RAW_RESPONSE_SAVED_MUST_BE_FALSE")
    if manifest.base64_emitted:
        blockers.append("BASE64_EMITTED_MUST_BE_FALSE")
    if manifest.real_api_allowed and not manifest.check_only:
        warnings.append("REAL_API_ALLOWED_WITHOUT_CHECK_ONLY")

    return {
        "valid": not blockers,
        "warnings": warnings,
        "blockers": blockers,
        "manifest_summary": safe_request_manifest_summary(manifest),
    }


def safe_request_manifest_summary(manifest: SingleQwenRequestManifest) -> dict:
    return {
        "request_id": manifest.request_id,
        "image_id": manifest.image_id,
        "image_sha256_prefix": manifest.image_sha256[:12] if manifest.image_sha256 else "",
        "manifest_valid": manifest.manifest_valid,
        "roi_valid": manifest.roi_valid,
        "prompt_version": manifest.prompt_version,
        "engine_name": manifest.engine_name,
        "real_api_allowed": manifest.real_api_allowed,
        "check_only": manifest.check_only,
        "raw_response_saved": manifest.raw_response_saved,
        "base64_emitted": manifest.base64_emitted,
        "api_key_present": manifest.api_key_present,
    }
