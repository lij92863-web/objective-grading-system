"""Manual ROI JSON schema and validator for single-image dry runs."""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ManualROI:
    roi_id: str = ""
    roi_type: str = ""
    question_id: str = ""
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    label: str = ""
    required: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManualROI":
        return cls(**{field_name: data.get(field_name, getattr(cls(), field_name))
                      for field_name in cls.__dataclass_fields__})


@dataclass
class ManualROIFile:
    roi_version: int = 1
    template_id: str = ""
    image_id: str = ""
    coordinate_space: str = "pixel"
    page_width: int = 0
    page_height: int = 0
    identity_rois: List[ManualROI] = field(default_factory=list)
    question_rois: List[ManualROI] = field(default_factory=list)
    choice_cell_rois: List[ManualROI] = field(default_factory=list)
    blank_rois: List[ManualROI] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManualROIFile":
        return cls(
            roi_version=data.get("roi_version", 1),
            template_id=data.get("template_id", ""),
            image_id=data.get("image_id", ""),
            coordinate_space=data.get("coordinate_space", "pixel"),
            page_width=data.get("page_width", 0),
            page_height=data.get("page_height", 0),
            identity_rois=[ManualROI.from_dict(item) for item in data.get("identity_rois", [])],
            question_rois=[ManualROI.from_dict(item) for item in data.get("question_rois", [])],
            choice_cell_rois=[ManualROI.from_dict(item) for item in data.get("choice_cell_rois", [])],
            blank_rois=[ManualROI.from_dict(item) for item in data.get("blank_rois", [])],
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def all_rois(self) -> List[ManualROI]:
        return self.identity_rois + self.question_rois + self.choice_cell_rois + self.blank_rois


def load_manual_roi_file(path: str | Path) -> ManualROIFile:
    return ManualROIFile.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def validate_manual_roi_file(roi_file: ManualROIFile) -> dict:
    blockers: List[str] = []
    warnings: List[str] = []
    if roi_file.page_width <= 0 or roi_file.page_height <= 0:
        blockers.append("INVALID_PAGE_BOUNDS")
    if not roi_file.identity_rois:
        blockers.append("MISSING_IDENTITY_ROI")
    if not roi_file.question_rois and not roi_file.choice_cell_rois and not roi_file.blank_rois:
        blockers.append("MISSING_QUESTION_ROIS")
    if not roi_file.choice_cell_rois and not roi_file.question_rois:
        warnings.append("NO_CHOICE_CELL_ROIS")
    if not roi_file.blank_rois:
        warnings.append("NO_BLANK_ROIS")
    for roi in roi_file.all_rois():
        blockers.extend(_validate_roi(roi, roi_file.page_width, roi_file.page_height))
    return {
        "valid": not blockers,
        "warnings": warnings,
        "blockers": blockers,
        "roi_summary": safe_roi_summary(roi_file),
    }


def safe_roi_summary(roi_file: ManualROIFile) -> dict:
    return {
        "roi_version": roi_file.roi_version,
        "template_id": roi_file.template_id,
        "image_id": roi_file.image_id,
        "coordinate_space": roi_file.coordinate_space,
        "page_width": roi_file.page_width,
        "page_height": roi_file.page_height,
        "identity_roi_count": len(roi_file.identity_rois),
        "question_roi_count": len(roi_file.question_rois),
        "choice_cell_roi_count": len(roi_file.choice_cell_rois),
        "blank_roi_count": len(roi_file.blank_rois),
        "total_roi_count": len(roi_file.all_rois()),
    }


def _validate_roi(roi: ManualROI, page_width: int, page_height: int) -> List[str]:
    blockers: List[str] = []
    label = roi.roi_id or roi.label or "UNKNOWN_ROI"
    if roi.x < 0 or roi.y < 0:
        blockers.append(f"NEGATIVE_COORDINATE:{label}")
    if roi.width <= 0 or roi.height <= 0:
        blockers.append(f"INVALID_ROI_SIZE:{label}")
    if roi.x + roi.width > page_width or roi.y + roi.height > page_height:
        blockers.append(f"ROI_OUT_OF_BOUNDS:{label}")
    if roi.required and not roi.roi_id:
        blockers.append("REQUIRED_ROI_MISSING_ID")
    return blockers
