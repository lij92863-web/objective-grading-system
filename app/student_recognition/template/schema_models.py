"""Explicit value objects for the TemplateProfile v2 protocol.

These frozen objects describe schema structure only.  They perform no image
processing or recognition and serialize to the same plain dictionaries used by
``TemplateProfile`` persistence.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ROIBox:
    x: float
    y: float
    w: float
    h: float

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ROIBox":
        return cls(*(float(data[key]) for key in ("x", "y", "w", "h")))


@dataclass(frozen=True)
class CoordinateSystem:
    type: str = "normalized"
    origin: str = "top_left"
    unit: str = "ratio"
    x_range: tuple = (0.0, 1.0)
    y_range: tuple = (0.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "origin": self.origin,
            "unit": self.unit,
            "x_range": list(self.x_range),
            "y_range": list(self.y_range),
        }


@dataclass(frozen=True)
class ReferenceCanvas:
    width: int
    height: int
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {"width": self.width, "height": self.height, "source": self.source}


@dataclass(frozen=True)
class Anchor:
    anchor_id: str
    x: float
    y: float
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"anchor_id": self.anchor_id, "x": self.x, "y": self.y}
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass(frozen=True)
class BubbleGrid:
    row_gap: float
    option_gap: float
    cell_w: float
    cell_h: float
    columns: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_gap": self.row_gap,
            "option_gap": self.option_gap,
            "cell_w": self.cell_w,
            "cell_h": self.cell_h,
            "columns": self.columns,
        }


@dataclass(frozen=True)
class QuestionBlock:
    block_id: str
    question_type: str
    question_range: List[int]
    options: List[str]
    anchor_id: str
    layout: BubbleGrid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "question_type": self.question_type,
            "question_range": list(self.question_range),
            "options": list(self.options),
            "anchor_id": self.anchor_id,
            "layout": self.layout.to_dict(),
        }


@dataclass(frozen=True)
class IdentityRegion:
    student_id_roi: Optional[ROIBox] = None
    name_roi: Optional[ROIBox] = None
    combined_identity_roi: Optional[ROIBox] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            key: roi.to_dict()
            for key, roi in (
                ("student_id_roi", self.student_id_roi),
                ("name_roi", self.name_roi),
                ("combined_identity_roi", self.combined_identity_roi),
            )
            if roi is not None
        }


@dataclass(frozen=True)
class BlankROI:
    question_no: int
    roi: ROIBox

    def to_dict(self) -> Dict[str, Any]:
        return {"question_no": self.question_no, "roi": self.roi.to_dict()}


@dataclass(frozen=True)
class TemplatePage:
    template_page_id: str
    page_no: int
    anchors: List[Anchor] = field(default_factory=list)
    identity: IdentityRegion = field(default_factory=IdentityRegion)
    question_blocks: List[QuestionBlock] = field(default_factory=list)
    blank_rois: List[BlankROI] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_page_id": self.template_page_id,
            "page_no": self.page_no,
            "anchors": [item.to_dict() for item in self.anchors],
            "identity": self.identity.to_dict(),
            "question_blocks": [item.to_dict() for item in self.question_blocks],
            "blank_rois": [item.to_dict() for item in self.blank_rois],
        }


__all__ = [
    "ROIBox", "CoordinateSystem", "ReferenceCanvas", "Anchor", "BubbleGrid",
    "QuestionBlock", "IdentityRegion", "BlankROI", "TemplatePage",
]
