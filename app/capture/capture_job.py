import dataclasses
from enum import Enum

from .capture_source import CaptureSourceType


class CaptureJobState(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    IMAGE_READY = "IMAGE_READY"
    QUALITY_FAILED = "QUALITY_FAILED"
    PAGE_FAILED = "PAGE_FAILED"
    RECOGNIZED = "RECOGNIZED"
    PROVISIONAL_SCORED = "PROVISIONAL_SCORED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CONFIRMED = "CONFIRMED"
    EXCLUDED = "EXCLUDED"
    FAILED = "FAILED"


@dataclasses.dataclass(frozen=True)
class CaptureJob:
    capture_job_id: str
    session_id: str
    class_id: str
    source_type: CaptureSourceType
    source_path: str
    stored_image_path: str
    sha256: str
    source_size: int
    source_mtime: float
    state: CaptureJobState
    created_at: str
    updated_at: str
    error_code: str = ""
