"""Template validation (SRE945-B).

``TemplateDraft.finalize()`` runs the :class:`TemplateValidator`, which produces a
structured :class:`ValidationReport`. Invalid templates fail closed: the draft
cannot become a :class:`~app.student_recognition.template.template_profile.TemplateProfile`.

Every error/warning carries a constitutional :class:`ErrorCode`; the human
message always comes from the catalog via
:func:`app.student_recognition.errors.error_message.message_for` (constitution
B6 -- never a free-form string).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_message import message_for
from app.student_recognition.template.anchor_layout import expand_block
from app.student_recognition.template.coordinates import is_finite_number
from app.student_recognition.template.template_profile import (
    _IDENTITY_KEYS,
    valid_coordinate_system,
)

__all__ = [
    "ValidationIssue",
    "ValidationReport",
    "TemplateValidationError",
    "TemplateValidator",
]

# Overlap (IoU) threshold above which two identity ROIs emit a warning.
_OVERLAP_WARNING_THRESHOLD = 0.5
# Tolerance for normalized bound checks (float rounding).
_BOUND_TOLERANCE = 1e-6


@dataclass
class ValidationIssue:
    """A single validation finding (error or warning)."""

    code: ErrorCode
    message: str
    path: str


@dataclass
class ValidationReport:
    """Result of validating a template."""

    status: str  # "valid" | "invalid"
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    @classmethod
    def invalid(cls, errors: List[ValidationIssue]) -> "ValidationReport":
        return cls(status="invalid", errors=list(errors), warnings=[])

    @classmethod
    def valid(cls, warnings: Optional[List[ValidationIssue]] = None) -> "ValidationReport":
        return cls(status="valid", errors=[], warnings=list(warnings or []))

    def is_valid(self) -> bool:
        return self.status == "valid"


class TemplateValidationError(ValueError):
    """Raised when a draft/profile fails validation.

    Always wraps a :class:`ValidationReport` whose ``errors`` carry constitutional
    ``ErrorCode`` members (no free-form reason strings, B6).
    """

    def __init__(self, report: ValidationReport) -> None:
        super().__init__(report.errors[0].message if report.errors else "template invalid")
        self.report: ValidationReport = report


def _issue(code: ErrorCode, path: str) -> ValidationIssue:
    return ValidationIssue(code, message_for(code), path)


class TemplateValidator:
    """Validates a :class:`TemplateProfile` (normalized coordinates)."""

    def validate(
        self, profile: "TemplateProfile"
    ) -> ValidationReport:
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []

        if not valid_coordinate_system(profile.coordinate_system):
            errors.append(_issue(ErrorCode.TEMPLATE_COORDINATE_SYSTEM_INVALID, "coordinate_system"))

        seen_page_ids: set = set()
        seen_page_nos: set = set()
        all_question_nos: List[int] = []

        for pi, page in enumerate(profile.pages):
            ppath = f"pages[{pi}]"
            pid = page.get("template_page_id")
            pno = page.get("page_no")
            if pid is not None:
                if pid in seen_page_ids:
                    errors.append(_issue(ErrorCode.TEMPLATE_DUPLICATE_PAGE_ID, f"{ppath}.template_page_id"))
                seen_page_ids.add(pid)
            if pno is not None:
                if pno in seen_page_nos:
                    errors.append(_issue(ErrorCode.TEMPLATE_DUPLICATE_PAGE_NO, f"{ppath}.page_no"))
                seen_page_nos.add(pno)

            identity = page.get("identity", {}) or {}
            if not any(identity.get(k) for k in _IDENTITY_KEYS):
                errors.append(_issue(ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING, f"{ppath}.identity"))
            else:
                present = [identity[k] for k in _IDENTITY_KEYS if identity.get(k)]
                for k in _IDENTITY_KEYS:
                    roi = identity.get(k)
                    if roi:
                        self._check_roi(roi, f"{ppath}.identity.{k}", errors)
                self._check_identity_overlap(present, f"{ppath}.identity", warnings)

            anchors = {a.get("anchor_id"): a for a in page.get("anchors", []) or []}
            for ai, a in enumerate(page.get("anchors", []) or []):
                self._check_point(a, f"{ppath}.anchors[{ai}]", errors)

            blocks = page.get("question_blocks", []) or []
            if len(blocks) == 0 and not page.get("blank_rois"):
                errors.append(_issue(ErrorCode.TEMPLATE_QUESTION_BLOCK_EMPTY, f"{ppath}.question_blocks"))

            for bi, block in enumerate(blocks):
                self._validate_block(block, anchors, f"{ppath}.question_blocks[{bi}]", errors, all_question_nos)

            for ri, roi in enumerate(page.get("blank_rois", []) or []):
                self._check_roi(roi, f"{ppath}.blank_rois[{ri}]", errors)

        if all_question_nos and len(all_question_nos) != len(set(all_question_nos)):
            errors.append(_issue(ErrorCode.TEMPLATE_DUPLICATE_QUESTION_NO, "pages"))

        if errors:
            return ValidationReport(status="invalid", errors=errors, warnings=warnings)
        return ValidationReport(status="valid", errors=[], warnings=warnings)

    # ------------------------------------------------------------------ #
    # Per-field checks
    # ------------------------------------------------------------------ #
    def _check_roi(self, roi: Any, path: str, errors: List[ValidationIssue]) -> None:
        if not isinstance(roi, dict):
            errors.append(_issue(ErrorCode.TEMPLATE_ROI_INVALID, path))
            return
        for key in ("x", "y", "w", "h"):
            v = roi.get(key)
            if v is None or isinstance(v, bool) or not is_finite_number(v):
                errors.append(_issue(ErrorCode.TEMPLATE_ROI_INVALID, f"{path}.{key}"))
                return
        x, y, w, h = float(roi["x"]), float(roi["y"]), float(roi["w"]), float(roi["h"])
        if w <= 0 or h <= 0:
            errors.append(_issue(ErrorCode.TEMPLATE_ROI_INVALID, path))
            return
        if (
            x < -_BOUND_TOLERANCE
            or y < -_BOUND_TOLERANCE
            or (x + w) > (1.0 + _BOUND_TOLERANCE)
            or (y + h) > (1.0 + _BOUND_TOLERANCE)
        ):
            errors.append(_issue(ErrorCode.TEMPLATE_ROI_OUT_OF_BOUNDS, path))

    def _check_point(self, point: Any, path: str, errors: List[ValidationIssue]) -> None:
        if not isinstance(point, dict):
            errors.append(_issue(ErrorCode.TEMPLATE_ROI_INVALID, path))
            return
        for key in ("x", "y"):
            v = point.get(key)
            if v is None or isinstance(v, bool) or not is_finite_number(v):
                errors.append(_issue(ErrorCode.TEMPLATE_ROI_INVALID, f"{path}.{key}"))
                return
            if float(v) < -_BOUND_TOLERANCE or float(v) > (1.0 + _BOUND_TOLERANCE):
                errors.append(_issue(ErrorCode.TEMPLATE_ROI_OUT_OF_BOUNDS, f"{path}.{key}"))

    def _validate_block(
        self,
        block: Dict[str, Any],
        anchors: Dict[str, Any],
        path: str,
        errors: List[ValidationIssue],
        all_question_nos: List[int],
    ) -> None:
        qtype = block.get("question_type")
        options = block.get("options") or []
        if not isinstance(options, list) or len(options) == 0:
            # An empty option list is reported with the type-specific code so the
            # consumer can surface a precise remediation hint.
            if qtype == "multi_choice":
                errors.append(
                    _issue(ErrorCode.TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS, f"{path}.options")
                )
            else:
                errors.append(_issue(ErrorCode.TEMPLATE_OPTION_CELL_MISSING, f"{path}.options"))
            return
        # Option labels must be strings.
        for oi, label in enumerate(options):
            if not isinstance(label, str):
                errors.append(_issue(ErrorCode.TEMPLATE_INVALID_OPTION_LABEL, f"{path}.options[{oi}]"))
        if qtype == "single_choice":
            if set(options) < {"A", "B", "C", "D"}:
                errors.append(_issue(ErrorCode.TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS, f"{path}.options"))
        elif qtype == "multi_choice":
            if len(options) == 0:
                errors.append(_issue(ErrorCode.TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS, f"{path}.options"))

        anchor_id = block.get("anchor_id")
        if anchor_id not in anchors:
            errors.append(_issue(ErrorCode.TEMPLATE_OPTION_CELL_MISSING, f"{path}.anchor_id"))
            return
        try:
            cells, blanks = expand_block(block, anchors)
        except (ValueError, KeyError) as exc:
            errors.append(_issue(ErrorCode.TEMPLATE_OPTION_CELL_MISSING, f"{path}: {exc}"))
            return
        if len(cells) == 0:
            errors.append(_issue(ErrorCode.TEMPLATE_OPTION_CELL_MISSING, path))
            return
        # A single block legitimately repeats each question_no once per option
        # cell, so de-duplicate within the block before accumulating; the
        # cross-block check below then flags a question that appears in two
        # different blocks.
        block_question_nos: set = set()
        for cell in cells:
            self._check_roi(cell.roi, f"{path}.options", errors)
            block_question_nos.add(cell.question_no)
        all_question_nos.extend(sorted(block_question_nos))
        for qno, roi in blanks.items():
            self._check_roi(roi, f"{path}.blank_roi[{qno}]", errors)

    def _check_identity_overlap(
        self, rois: List[Dict[str, Any]], path: str, warnings: List[ValidationIssue]
    ) -> None:
        for i in range(len(rois)):
            for j in range(i + 1, len(rois)):
                iou = _iou(rois[i], rois[j])
                if iou > _OVERLAP_WARNING_THRESHOLD:
                    warnings.append(_issue(ErrorCode.TEMPLATE_ROI_OVERLAP_WARNING, path))


def _iou(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """Intersection-over-union of two normalized ROIs."""
    ax2 = float(a["x"]) + float(a["w"])
    ay2 = float(a["y"]) + float(a["h"])
    bx2 = float(b["x"]) + float(b["w"])
    by2 = float(b["y"]) + float(b["h"])
    ix1 = max(float(a["x"]), float(b["x"]))
    iy1 = max(float(a["y"]), float(b["y"]))
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    union = (ax2 - float(a["x"])) * (ay2 - float(a["y"])) + (bx2 - float(b["x"])) * (
        by2 - float(b["y"])
    ) - inter
    if union <= 0.0:
        return 0.0
    return inter / union
