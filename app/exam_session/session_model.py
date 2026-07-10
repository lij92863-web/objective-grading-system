import dataclasses
from enum import Enum


class ExamSessionState(str, Enum):
    DRAFT = "DRAFT"
    CLASS_SELECTED = "CLASS_SELECTED"
    ASSET_READY = "ASSET_READY"
    CAPTURE_READY = "CAPTURE_READY"
    CAPTURING = "CAPTURING"
    PROCESSING = "PROCESSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    READY_TO_FINALIZE = "READY_TO_FINALIZE"
    FINALIZED = "FINALIZED"
    ARCHIVED = "ARCHIVED"


@dataclasses.dataclass(frozen=True)
class ExamSession:
    session_id: str
    exam_name: str
    class_id: str
    answer_key_asset_id: str | None
    paper_asset_id: str | None
    template_id: str | None
    teacher_confirmed: bool
    state: ExamSessionState
    created_at: str
    updated_at: str
