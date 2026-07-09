"""Single anonymous image manifest contract."""
import base64
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
FORBIDDEN_KEYS = {"base64", "image_base64", "raw_response", "api_key"}


@dataclass
class SingleImageManifest:
    manifest_version: int = 1
    image_id: str = ""
    image_path: str = ""
    image_sha256: str = ""
    mime_type: str = ""
    file_size_bytes: int = 0
    is_anonymous: bool = False
    contains_real_student_data: bool = True
    template_id: str = ""
    roi_file: str = ""
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SingleImageManifest":
        unknown_forbidden = sorted(FORBIDDEN_KEYS & set(data))
        if unknown_forbidden:
            raise ValueError(f"manifest contains forbidden fields: {unknown_forbidden}")
        return cls(**{field_name: data.get(field_name, getattr(cls(), field_name))
                      for field_name in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_single_image_manifest(path: str | Path) -> SingleImageManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return SingleImageManifest.from_dict(data)


def validate_single_image_manifest(manifest: SingleImageManifest) -> dict:
    blockers: List[str] = []
    warnings: List[str] = []
    raw = json.dumps(manifest.to_dict(), ensure_ascii=False)
    if "data:image" in raw or _looks_like_base64_payload(raw):
        blockers.append("MANIFEST_CONTAINS_BASE64")
    if "sk-" in raw or "Bearer " in raw:
        blockers.append("MANIFEST_CONTAINS_SECRET")
    if not manifest.image_id:
        blockers.append("MISSING_IMAGE_ID")
    if not manifest.image_path:
        blockers.append("MISSING_IMAGE_PATH")
    if not manifest.is_anonymous:
        blockers.append("IMAGE_NOT_ANONYMOUS")
    if manifest.contains_real_student_data:
        blockers.append("REAL_STUDENT_DATA_PRESENT")
    if manifest.mime_type not in ALLOWED_MIME_TYPES:
        blockers.append("UNSUPPORTED_MIME_TYPE")
    if manifest.file_size_bytes <= 0:
        blockers.append("INVALID_FILE_SIZE")
    if not manifest.template_id:
        warnings.append("MISSING_TEMPLATE_ID")
    if not manifest.roi_file:
        warnings.append("MISSING_ROI_FILE")
    image_path = Path(manifest.image_path) if manifest.image_path else None
    if image_path and not image_path.exists():
        warnings.append("IMAGE_FILE_NOT_PRESENT_FOR_DRY_RUN")
    return {
        "valid": not blockers,
        "warnings": warnings,
        "blockers": blockers,
        "manifest_summary": safe_manifest_summary(manifest),
    }


def safe_manifest_summary(manifest: SingleImageManifest) -> dict:
    return {
        "manifest_version": manifest.manifest_version,
        "image_id": manifest.image_id,
        "image_name": Path(manifest.image_path).name if manifest.image_path else "",
        "image_sha256_prefix": manifest.image_sha256[:12],
        "mime_type": manifest.mime_type,
        "file_size_bytes": manifest.file_size_bytes,
        "is_anonymous": manifest.is_anonymous,
        "contains_real_student_data": manifest.contains_real_student_data,
        "template_id": manifest.template_id,
        "roi_file": Path(manifest.roi_file).name if manifest.roi_file else "",
    }


def _looks_like_base64_payload(value: str) -> bool:
    compact = "".join(value.split())
    if len(compact) < 160:
        return False
    try:
        base64.b64decode(compact, validate=True)
        return True
    except Exception:
        return False
