"""R23: Qwen request builder — no base64, no API key in output."""
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

SUPPORTED_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@dataclass
class QwenRequestMetadata:
    image_path: str = ""
    sha256: str = ""
    mime_type: str = ""
    file_size: int = 0
    is_valid: bool = False
    errors: list = field(default_factory=list)


def build_qwen_request_metadata(image_path: str, max_bytes: int = 10*1024*1024) -> QwenRequestMetadata:
    p = Path(image_path)
    errors = []
    if not p.exists():
        return QwenRequestMetadata(image_path=str(p), errors=["FILE_NOT_FOUND"])
    size = p.stat().st_size
    if size == 0:
        errors.append("FILE_EMPTY")
    if size > max_bytes:
        errors.append("FILE_TOO_LARGE")
    suffix = p.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
    mime_type = mime.get(suffix.lstrip("."), "")
    if not mime_type:
        errors.append("UNSUPPORTED_MIME")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    return QwenRequestMetadata(image_path=str(p), sha256=sha, mime_type=mime_type,
                                file_size=size, is_valid=len(errors) == 0, errors=errors)
