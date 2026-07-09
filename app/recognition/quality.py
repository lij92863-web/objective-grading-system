"""Image quality — no OpenCV/Pillow, stdlib only."""
import hashlib
from pathlib import Path
from .contracts import ImageAsset, ImageQualityReport

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer_mime_type(path: Path) -> str:
    m = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp"}
    return m.get(path.suffix.lower(), "application/octet-stream")


def build_image_asset(path, source_kind="fixture") -> ImageAsset:
    p = Path(path)
    if not p.exists():
        return ImageAsset(asset_id=str(p), file_path=str(p), source_kind=source_kind)
    return ImageAsset(asset_id=p.stem, file_path=str(p), sha256=compute_sha256(p),
                      mime_type=infer_mime_type(p), source_kind=source_kind)


def validate_image_asset(asset: ImageAsset) -> ImageQualityReport:
    reasons = []
    p = Path(asset.file_path)
    if not p.exists(): reasons.append("IMAGE_MISSING")
    elif p.stat().st_size == 0: reasons.append("IMAGE_EMPTY")
    if p.suffix.lower() not in SUPPORTED_SUFFIXES: reasons.append("IMAGE_UNSUPPORTED")
    is_valid = len(reasons) == 0
    return ImageQualityReport(asset_id=asset.asset_id, is_valid=is_valid,
                              status="ok" if is_valid else "blocking",
                              reasons=reasons, sha256=asset.sha256,
                              mime_type=asset.mime_type, file_size=p.stat().st_size if p.exists() else 0)


def build_quality_report(asset: ImageAsset) -> ImageQualityReport:
    return validate_image_asset(asset)
