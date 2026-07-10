"""Synthetic (SRE121) v1 -> TemplateProfile v2 adapter (SRE945-D).

The existing :class:`app.student_recognition.synthetic.template_profile.TemplateProfile`
is left **untouched** (its pixel geometry keeps SRE121's 123 tests green). This
module is the *only* place that translates that pixel geometry into the
normalized v2 protocol, by dividing every pixel coordinate by the canvas size.

This keeps the v2 layer fully backwards compatible: a legacy synthetic
``template_profile.json`` (``schema_version == 1``) is recognized and promoted
automatically by :meth:`TemplateProfile.from_dict`.
"""

from typing import Any, Dict, Optional

from app.student_recognition.template.template_profile import (
    SCHEMA_VERSION,
    _COORDINATE_SYSTEM,
    TemplateProfile,
)

__all__ = ["adapt_synthetic_to_v2"]

# Anchor id used for the single derived anchor of a synthetic-promoted template.
_SYNTH_ANCHOR_ID = "choice_block_top_left"
# Block id used for the single derived question block.
_SYNTH_BLOCK_ID = "choice_block_1"
# Page id used for the single derived page.
_SYNTH_PAGE_ID = "page_1"


def adapt_synthetic_to_v2(
    synth: Any,
    template_id: Optional[str] = None,
    template_name: Optional[str] = None,
) -> TemplateProfile:
    """Convert a synthetic v1 profile into a normalized v2 ``TemplateProfile``.

    Args:
        synth: A ``synthetic.template_profile.TemplateProfile`` instance.
        template_id: Override the resulting v2 ``template_id`` (defaults to the
            synthetic id, e.g. ``"synthetic-v1"``).
        template_name: Override the human-readable name.

    Returns:
        A validated-by-construction v2 ``TemplateProfile``.
    """
    canvas = synth.canvas
    cw = float(canvas["width"])
    ch = float(canvas["height"])
    grid = synth.bubble_grid
    origin_x = float(grid["origin_x"])
    origin_y = float(grid["origin_y"])
    cell_w = float(grid["cell_w"])
    cell_h = float(grid["cell_h"])
    cols = int(grid["cols"])
    rows = int(grid["rows"])
    options = [str(o) for o in (grid.get("option_labels") or ["A", "B", "C", "D"])]

    anchor = {
        "anchor_id": _SYNTH_ANCHOR_ID,
        "x": origin_x / cw,
        "y": origin_y / ch,
        "description": "选择题区域左上角（由 synthetic origin 推导）",
    }
    layout: Dict[str, Any] = {
        "row_gap": cell_h / ch,
        "option_gap": cell_w / cw,
        "cell_w": cell_w / cw,
        "cell_h": cell_h / ch,
        "columns": 1,
    }
    block = {
        "block_id": _SYNTH_BLOCK_ID,
        "question_type": "single_choice" if cols == 4 else "multi_choice",
        "question_range": [1, rows],
        "options": options,
        "anchor_id": _SYNTH_ANCHOR_ID,
        "layout": layout,
        "blank_roi": {
            "dx": 0.0,
            "dy": 0.0,
            "w": (cell_w * cols) / cw,
            "h": 0.03,
        },
    }

    id_roi = synth.identity_roi
    # Split the identity band into a left (student id) and right (name) half so
    # the two ROIs don't overlap (avoids a false overlap warning), plus their
    # union as the combined identity ROI.
    half_w = float(id_roi["w"]) / 2.0
    student_id_roi = {
        "x": float(id_roi["x"]) / cw,
        "y": float(id_roi["y"]) / ch,
        "w": half_w / cw,
        "h": float(id_roi["h"]) / ch,
    }
    name_roi = {
        "x": (float(id_roi["x"]) + half_w) / cw,
        "y": float(id_roi["y"]) / ch,
        "w": half_w / cw,
        "h": float(id_roi["h"]) / ch,
    }
    combined_identity_roi = _norm_roi(id_roi, cw, ch)
    identity = {
        "student_id_roi": student_id_roi,
        "name_roi": name_roi,
        "combined_identity_roi": combined_identity_roi,
    }

    page = {
        "template_page_id": _SYNTH_PAGE_ID,
        "page_no": 1,
        "anchors": [anchor],
        "identity": identity,
        "question_blocks": [block],
        "blank_rois": [],
    }

    data = {
        "schema_version": SCHEMA_VERSION,
        "template_id": template_id or synth.template_id,
        "template_name": template_name or f"{synth.template_id} (v2)",
        "template_version": int(synth.template_version),
        "created_at": None,
        "updated_at": None,
        "coordinate_system": dict(_COORDINATE_SYSTEM),
        "reference_canvas": {
            "width": int(cw),
            "height": int(ch),
            "source": f"synthetic:{synth.template_id}",
        },
        "pages": [page],
    }
    return TemplateProfile.from_dict(data)


def _norm_roi(pixel_roi: Dict[str, Any], cw: float, ch: float) -> Dict[str, float]:
    """Normalize a pixel ROI by the canvas size."""
    return {
        "x": float(pixel_roi["x"]) / cw,
        "y": float(pixel_roi["y"]) / ch,
        "w": float(pixel_roi["w"]) / cw,
        "h": float(pixel_roi["h"]) / ch,
    }
