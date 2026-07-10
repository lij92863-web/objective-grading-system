"""TemplateProfile v2 -- the canonical, normalized template protocol (SRE945).

A ``TemplateProfile`` is the *single source of truth* for where every option
bubble, identity region and blank writing area lives on an answer sheet. All
coordinates are **normalized** (x, y, w, h in [0, 1], origin top-left). Pixel
coordinates are only ever derived at runtime via
:func:`app.student_recognition.template.coordinates.to_runtime_pixels`.

This module is a *low-level* geometric module: it performs no recognition, no
image correction and no grading, and it does not import any forbidden
upper-layer module (constitution B10 / §13). Downstream OMR (SRE341) and
ImageNorm (SRE221) consume coordinates exclusively through the frozen interface
methods (``get_option_cells`` / ``get_identity_roi`` / ``get_blank_roi``).
"""

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_message import message_for

__all__ = [
    "SCHEMA_VERSION",
    "OptionCell",
    "TemplateRef",
    "TemplateProfile",
    "export_template",
    "import_template",
    "_COORDINATE_SYSTEM",
    "_IDENTITY_KEYS",
    "valid_coordinate_system",
    "union_roi",
    "deep_copy_page",
]


# v2 schema version is a *string* ("2.0"); v1 (int 1, synthetic) is auto-adapted.
SCHEMA_VERSION: str = "2.0"

# Canonical valid coordinate-system descriptor.
_COORDINATE_SYSTEM: Dict[str, Any] = {
    "type": "normalized",
    "origin": "top_left",
    "unit": "ratio",
    "x_range": [0.0, 1.0],
    "y_range": [0.0, 1.0],
}

# Accepted identity ROI keys (at least one must be present on every page).
_IDENTITY_KEYS = ("student_id_roi", "name_roi", "combined_identity_roi")

# Canonical question-type vocabulary.
SINGLE_CHOICE = "single_choice"
MULTI_CHOICE = "multi_choice"
_REQUIRED_SINGLE_CHOICE_LABELS = ("A", "B", "C", "D")


@dataclass(frozen=True)
class OptionCell:
    """A single option bubble cell, identified by question + label.

    ``roi`` is normalized ``{"x", "y", "w", "h"}`` (all values in [0, 1]).
    """

    question_no: int
    option_label: str
    roi: Dict[str, float]


@dataclass(frozen=True)
class TemplateRef:
    """Immutable reference to a specific template version (for CaptureJob etc.)."""

    template_id: str
    template_version: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_version": self.template_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateRef":
        return cls(
            template_id=str(data["template_id"]),
            template_version=int(data["template_version"]),
        )


def valid_coordinate_system(coord: Any) -> bool:
    """Return True if *coord* describes a legal normalized coordinate system."""
    if not isinstance(coord, dict):
        return False
    return (
        coord.get("type") == "normalized"
        and coord.get("origin") == "top_left"
        and coord.get("unit") == "ratio"
    )


def union_roi(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, float]:
    """Return the bounding box of two normalized ROIs ``a`` and ``b``."""
    x1 = min(float(a["x"]), float(b["x"]))
    y1 = min(float(a["y"]), float(b["y"]))
    x2 = max(float(a["x"]) + float(a["w"]), float(b["x"]) + float(b["w"]))
    y2 = max(float(a["y"]) + float(a["h"]), float(b["y"]) + float(b["h"]))
    return {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1}


def deep_copy_page(page: Dict[str, Any]) -> Dict[str, Any]:
    """Return a deep copy of a page descriptor (defensive against mutation)."""
    return copy.deepcopy(page)


@dataclass(frozen=True)
class TemplateProfile:
    """Frozen, validated template protocol (normalized coordinates only)."""

    template_id: str
    template_version: int
    pages: List[Dict[str, Any]]
    reference_canvas: Dict[str, Any] = field(default_factory=dict)
    template_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    coordinate_system: Dict[str, Any] = field(
        default_factory=lambda: dict(_COORDINATE_SYSTEM)
    )
    schema_version: str = SCHEMA_VERSION

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary of this profile."""
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "template_version": self.template_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "coordinate_system": dict(self.coordinate_system),
            "reference_canvas": dict(self.reference_canvas),
            "pages": [deep_copy_page(p) for p in self.pages],
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], *, _validate: bool = True
    ) -> "TemplateProfile":
        """Build a ``TemplateProfile`` from a v2 dict (auto-adapting v1).

        Raises:
            TemplateValidationError: If a required top-level field is missing or
                the coordinate system is invalid. Every failure carries a
                constitutional :class:`ErrorCode` (no free-form strings, B6).
        """
        from app.student_recognition.template.template_validator import (
            TemplateValidationError,
            ValidationIssue,
            ValidationReport,
        )

        if not isinstance(data, dict):
            raise TemplateValidationError(
                ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_MISSING,
                            message_for(ErrorCode.TEMPLATE_MISSING),
                            "$",
                        )
                    ]
                )
            )

        sv = data.get("schema_version")
        # Auto-adapt synthetic v1 (int 1) into the v2 protocol.
        if sv == 1 or (isinstance(sv, str) and sv.strip() == "1"):
            from app.student_recognition.synthetic.template_profile import (
                TemplateProfile as SynthProfile,
            )
            from app.student_recognition.template.compatibility import (
                adapt_synthetic_to_v2,
            )

            synth = SynthProfile.from_dict(data)
            return adapt_synthetic_to_v2(synth)

        if sv is None:
            raise TemplateValidationError(
                ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_VERSION_MISSING,
                            message_for(ErrorCode.TEMPLATE_VERSION_MISSING),
                            "schema_version",
                        )
                    ]
                )
            )
        if str(sv) != SCHEMA_VERSION:
            raise TemplateValidationError(
                ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_VERSION_MISMATCH,
                            message_for(ErrorCode.TEMPLATE_VERSION_MISMATCH),
                            "schema_version",
                        )
                    ]
                )
            )
        if "template_id" not in data or not data.get("template_id"):
            raise TemplateValidationError(
                ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_MISSING,
                            message_for(ErrorCode.TEMPLATE_MISSING),
                            "template_id",
                        )
                    ]
                )
            )
        if "template_version" not in data:
            raise TemplateValidationError(
                ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_VERSION_MISSING,
                            message_for(ErrorCode.TEMPLATE_VERSION_MISSING),
                            "template_version",
                        )
                    ]
                )
            )
        # Structural contract only: the coordinate_system blob must be a complete
        # dict with the canonical fields. The *semantic* check (type == "normalized"
        # / origin / unit) is the validator's job (SRE945 design §7.1), so a
        # structurally complete but semantically wrong system is accepted here and
        # rejected by :class:`TemplateValidator`.
        coord = data.get("coordinate_system")
        if coord is None:
            coord = dict(_COORDINATE_SYSTEM)
        _COORD_REQUIRED = ("type", "origin", "unit", "x_range", "y_range")
        if not isinstance(coord, dict) or not all(k in coord for k in _COORD_REQUIRED):
            raise TemplateValidationError(
                ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_COORDINATE_SYSTEM_INVALID,
                            message_for(ErrorCode.TEMPLATE_COORDINATE_SYSTEM_INVALID),
                            "coordinate_system",
                        )
                    ]
                )
            )
        pages = data.get("pages")
        if not isinstance(pages, list) or len(pages) == 0:
            raise TemplateValidationError(
                ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_PAGE_MISSING,
                            message_for(ErrorCode.TEMPLATE_PAGE_MISSING),
                            "pages",
                        )
                    ]
                )
            )
        profile = cls(
            schema_version=SCHEMA_VERSION,
            template_id=str(data["template_id"]),
            template_name=data.get("template_name"),
            template_version=int(data["template_version"]),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            coordinate_system=dict(coord) if coord else dict(_COORDINATE_SYSTEM),
            reference_canvas=dict(data.get("reference_canvas", {})),
            pages=[deep_copy_page(p) for p in pages],
        )
        if _validate:
            from app.student_recognition.template.template_validator import TemplateValidator

            report = TemplateValidator().validate(profile)
            if not report.is_valid():
                raise TemplateValidationError(report)
        return profile

    # ------------------------------------------------------------------ #
    # Frozen OMR interface (normalized ROI only)
    # ------------------------------------------------------------------ #
    def _iter_blocks(self):
        """Yield ``(page, block)`` pairs across all pages."""
        for page in self.pages:
            for block in page.get("question_blocks", []) or []:
                yield page, block

    def get_option_cells(self, question_no: int) -> List[OptionCell]:
        """Return all option cells for *question_no* (normalized ROIs)."""
        from app.student_recognition.template.anchor_layout import expand_block

        cells: List[OptionCell] = []
        for page, block in self._iter_blocks():
            anchors = {
                a.get("anchor_id"): a for a in page.get("anchors", []) or []
            }
            block_cells, _ = expand_block(block, anchors)
            for cell in block_cells:
                if cell.question_no == question_no:
                    cells.append(cell)
        return cells

    def get_all_option_cells(self) -> List[OptionCell]:
        """Return every option cell across all questions (normalized ROIs)."""
        from app.student_recognition.template.anchor_layout import expand_block

        cells: List[OptionCell] = []
        for page, block in self._iter_blocks():
            anchors = {
                a.get("anchor_id"): a for a in page.get("anchors", []) or []
            }
            block_cells, _ = expand_block(block, anchors)
            cells.extend(block_cells)
        return cells

    def get_blank_roi(self, question_no: int) -> Optional[Dict[str, float]]:
        """Return the blank/书写 ROI for *question_no*, or None if absent."""
        from app.student_recognition.template.anchor_layout import expand_block

        for page, block in self._iter_blocks():
            anchors = {
                a.get("anchor_id"): a for a in page.get("anchors", []) or []
            }
            _, blanks = expand_block(block, anchors)
            if question_no in blanks:
                return blanks[question_no]
        return None

    def get_identity_roi(self) -> Dict[str, float]:
        """Return the effective identity ROI.

        Preference order: ``combined_identity_roi`` first; otherwise the union
        of ``student_id_roi`` and ``name_roi``; otherwise the single present ROI.
        """
        for page in self.pages:
            identity = page.get("identity", {}) or {}
            combined = identity.get("combined_identity_roi")
            if combined:
                return dict(combined)
            sid = identity.get("student_id_roi")
            name = identity.get("name_roi")
            if sid and name:
                return union_roi(sid, name)
            if sid:
                return dict(sid)
            if name:
                return dict(name)
        raise KeyError("template has no identity ROI on any page")

    def get_page_anchors(self, page_no: int) -> List[Dict[str, Any]]:
        """Return the anchors defined for the page with *page_no*."""
        page = self.get_page(page_no)
        if page is None:
            return []
        return list(page.get("anchors", []) or [])

    def get_page(self, page_no: int) -> Optional[Dict[str, Any]]:
        """Return the page descriptor with the given *page_no*, or None."""
        for page in self.pages:
            if page.get("page_no") == page_no:
                return page
        return None

    def question_count(self) -> int:
        """Return the total number of distinct questions across all blocks."""
        return len({cell.question_no for cell in self.get_all_option_cells()})

    def list_questions(self) -> List[int]:
        """Return sorted unique question numbers declared by the template."""
        return sorted({cell.question_no for cell in self.get_all_option_cells()})

    def get_question_block(self, question_no: int) -> Optional[Dict[str, Any]]:
        """Return a defensive copy of the block containing ``question_no``."""
        from app.student_recognition.template.anchor_layout import parse_question_range

        for _page, block in self._iter_blocks():
            if question_no in parse_question_range(block.get("question_range", [])):
                return copy.deepcopy(block)
        return None

    def get_template_ref(self) -> TemplateRef:
        """Return the immutable id/version reference for this profile."""
        return TemplateRef(self.template_id, self.template_version)

    def to_canonical_json(self) -> str:
        """Return stable UTF-8 JSON text for hashing, export and roundtrip."""
        return export_template(self)


def export_template(profile: TemplateProfile) -> str:
    """Serialize a profile using the canonical SRE945 JSON representation."""
    return json.dumps(
        profile.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def import_template(payload: "str | bytes | Dict[str, Any]") -> TemplateProfile:
    """Strictly import and validate v2 JSON or an explicitly supported v1 shape."""
    from app.student_recognition.template.template_validator import (
        TemplateValidationError,
        TemplateValidator,
        ValidationIssue,
        ValidationReport,
    )

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    data = json.loads(payload) if isinstance(payload, str) else copy.deepcopy(payload)
    unknown_path = _first_unknown_field(data)
    if unknown_path is not None:
        code = ErrorCode.TEMPLATE_SCHEMA_INVALID
        raise TemplateValidationError(
            ValidationReport.invalid([ValidationIssue(code, message_for(code), unknown_path)])
        )
    profile = TemplateProfile.from_dict(data)
    report = TemplateValidator().validate(profile)
    if not report.is_valid():
        raise TemplateValidationError(report)
    return profile


def _first_unknown_field(data: Any) -> Optional[str]:
    """Return the first unknown v2 field path; v1 is delegated to its adapter."""
    if not isinstance(data, dict) or data.get("schema_version") in (1, "1"):
        return None
    allowed_top = {
        "schema_version", "template_id", "template_name", "template_version",
        "created_at", "updated_at", "coordinate_system", "reference_canvas", "pages",
    }
    allowed_page = {
        "template_page_id", "page_no", "anchors", "identity",
        "question_blocks", "blank_rois",
    }
    allowed_block = {
        "block_id", "question_type", "question_range", "options", "anchor_id",
        "anchor_mode", "layout", "blank_roi",
    }
    allowed_layout = {"row_gap", "option_gap", "cell_w", "cell_h", "columns"}
    allowed_anchor = {"anchor_id", "x", "y", "description"}
    allowed_roi = {"x", "y", "w", "h", "question_no", "roi"}
    for key in data:
        if key not in allowed_top:
            return key
    for pi, page in enumerate(data.get("pages", []) or []):
        if not isinstance(page, dict):
            continue
        for key in page:
            if key not in allowed_page:
                return f"pages[{pi}].{key}"
        for ai, anchor in enumerate(page.get("anchors", []) or []):
            if isinstance(anchor, dict):
                for key in anchor:
                    if key not in allowed_anchor:
                        return f"pages[{pi}].anchors[{ai}].{key}"
        identity = page.get("identity", {}) or {}
        if isinstance(identity, dict):
            for name, roi in identity.items():
                if name not in _IDENTITY_KEYS:
                    return f"pages[{pi}].identity.{name}"
                if isinstance(roi, dict):
                    for key in roi:
                        if key not in allowed_roi:
                            return f"pages[{pi}].identity.{name}.{key}"
        for bi, block in enumerate(page.get("question_blocks", []) or []):
            if not isinstance(block, dict):
                continue
            for key in block:
                if key not in allowed_block:
                    return f"pages[{pi}].question_blocks[{bi}].{key}"
            layout = block.get("layout", {}) or {}
            if isinstance(layout, dict):
                for key in layout:
                    if key not in allowed_layout:
                        return f"pages[{pi}].question_blocks[{bi}].layout.{key}"
    return None
