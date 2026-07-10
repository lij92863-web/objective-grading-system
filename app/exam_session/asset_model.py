import dataclasses
from enum import Enum


class AssetType(str, Enum):
    ANSWER_KEY = "ANSWER_KEY"
    PAPER = "PAPER"
    TEMPLATE = "TEMPLATE"
    ANSWER_SHEET_SAMPLE = "ANSWER_SHEET_SAMPLE"
    OTHER = "OTHER"


@dataclasses.dataclass(frozen=True)
class ExamAsset:
    asset_id: str
    session_id: str
    class_id: str
    asset_type: AssetType
    original_filename: str
    stored_path: str
    sha256: str
    status: str
    created_at: str
    updated_at: str


@dataclasses.dataclass(frozen=True)
class AssetRegistration:
    asset: ExamAsset
    duplicate: bool = False
    warning: str = ""
