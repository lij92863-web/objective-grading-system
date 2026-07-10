"""SRE945 Level-1 (headless) calibrator.

The calibrator turns *inputs* (a synthetic template, or manual anchor/grid
definitions) into a validated, frozen :class:`TemplateProfile`. It contains no UI
and no image processing (constitution B5/B10). Two entry points:

* :meth:`Calibrator.calibrate_from_synthetic` -- promote a synthetic template via
  the v1->v2 compatibility adapter.
* :meth:`Calibrator.calibrate_from_anchors` -- build a template from explicit
  anchors + question blocks + identity (``grid_origin`` or ``four_corner`` mode).

Both return a :class:`TemplateProfile`; on validation failure they raise
:class:`TemplateValidationError` whose ``.report`` enumerates the blocking
:class:`ErrorCode` members (constitution B6 -- never a free-form string).
"""

from typing import Any, Dict, List, Optional

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_message import message_for
from app.student_recognition.synthetic.template_profile import (
    TemplateProfile as SyntheticTemplateProfile,
)
from app.student_recognition.template.anchor_layout import _require_corners
from app.student_recognition.template.compatibility import adapt_synthetic_to_v2
from app.student_recognition.template.template_profile import (
    SCHEMA_VERSION,
    TemplateProfile,
)
from app.student_recognition.template.template_validator import (
    TemplateValidationError,
    ValidationIssue,
    ValidationReport,
    TemplateValidator,
)

__all__ = ["Calibrator", "GRID_ORIGIN", "FOUR_CORNER"]

# Calibration modes for ``calibrate_from_anchors``.
GRID_ORIGIN = "grid_origin"
FOUR_CORNER = "four_corner"


class Calibrator:
    """Headless template calibrator (no UI, no image processing)."""

    # ------------------------------------------------------------------ #
    # Level 1a: synthetic promotion
    # ------------------------------------------------------------------ #
    @staticmethod
    def calibrate_from_synthetic(
        synthetic_profile: SyntheticTemplateProfile,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None,
    ) -> TemplateProfile:
        """Promote a synthetic (v1) template to a validated v2 TemplateProfile.

        Args:
            synthetic_profile: Source synthetic ``TemplateProfile``.
            template_id: Override the resulting v2 ``template_id`` (defaults to
                the synthetic id).
            template_name: Override the human-readable name.

        Returns:
            A validated, frozen :class:`TemplateProfile`.

        Raises:
            TemplateValidationError: If the promoted profile fails validation.
        """
        profile = adapt_synthetic_to_v2(
            synthetic_profile, template_id=template_id, template_name=template_name
        )
        report = TemplateValidator().validate(profile)
        if report.status != "valid":
            raise TemplateValidationError(report)
        return profile

    # ------------------------------------------------------------------ #
    # Level 1b: manual anchor + grid calibration
    # ------------------------------------------------------------------ #
    @staticmethod
    def calibrate_from_anchors(
        reference_canvas: Dict[str, Any],
        anchors: List[Dict[str, Any]],
        blocks: List[Dict[str, Any]],
        identity: Dict[str, Any],
        question_range: Optional[List[int]] = None,
        anchor_mode: str = GRID_ORIGIN,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None,
    ) -> TemplateProfile:
        """Build a TemplateProfile from explicit anchors + blocks + identity.

        Args:
            reference_canvas: Reference canvas ``{"width", "height", ...}``.
            anchors: List of anchor dicts (must include every anchor referenced
                by ``blocks``; for ``anchor_mode="four_corner"`` the four corner
                anchors must be present and well-formed).
            blocks: List of question-block dicts.
            identity: Identity ROI dict (``combined_identity_roi`` or
                ``student_id_roi`` / ``name_roi``).
            question_range: Default ``[start, end]`` applied to any block that
                does not declare its own ``question_range``.
            anchor_mode: ``"grid_origin"`` (default) or ``"four_corner"``.
            template_id: Override the resulting v2 ``template_id``.
            template_name: Override the human-readable name.

        Returns:
            A validated, frozen :class:`TemplateProfile`.

        Raises:
            TemplateValidationError: If the anchors are malformed (e.g. missing
                four-corner anchors) or the built template fails validation. The
                report carries the constitutional ``ErrorCode`` members.
        """
        anchors_by_id = {a.get("anchor_id"): a for a in anchors}

        if anchor_mode == FOUR_CORNER:
            try:
                _require_corners(anchors_by_id)
            except (ValueError, KeyError) as exc:
                report = ValidationReport.invalid(
                    [
                        ValidationIssue(
                            ErrorCode.TEMPLATE_CALIBRATION_ANCHOR_INVALID,
                            message_for(ErrorCode.TEMPLATE_CALIBRATION_ANCHOR_INVALID),
                            "anchors",
                        )
                    ]
                )
                raise TemplateValidationError(report) from exc

        v2_blocks: List[Dict[str, Any]] = []
        for block in blocks:
            b = dict(block)
            b.setdefault("anchor_mode", anchor_mode)
            if not b.get("question_range"):
                b["question_range"] = list(question_range or [1, 1])
            v2_blocks.append(b)

        page = {
            "template_page_id": "page_1",
            "page_no": 1,
            "anchors": list(anchors),
            "identity": dict(identity),
            "question_blocks": v2_blocks,
            "blank_rois": [],
        }

        data: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "template_id": template_id or "manual_calibration",
            "template_name": template_name or "Manual anchor calibration",
            "template_version": 1,
            "coordinate_system": {
                "type": "normalized",
                "origin": "top_left",
                "unit": "ratio",
                "x_range": [0.0, 1.0],
                "y_range": [0.0, 1.0],
            },
            "reference_canvas": {
                "width": int(reference_canvas["width"]),
                "height": int(reference_canvas["height"]),
                "source": reference_canvas.get("source", "manual:anchor"),
            },
            "pages": [page],
        }

        # Top-level structural validation (raises TemplateValidationError).
        profile = TemplateProfile.from_dict(data)
        report = TemplateValidator().validate(profile)
        if report.status != "valid":
            raise TemplateValidationError(report)
        return profile
