"""Anchor + BubbleGrid expansion (SRE945-C).

A ``TemplateProfile`` stores only *anchors* and *grid parameters*; the concrete
option-cell / blank ROIs are derived deterministically from those parameters by
:func:`expand_block`. This keeps the template DRY: moving a whole block means
editing one anchor, not re-listing every question's coordinates.

Two anchor modes are supported:

* ``grid_origin`` -- a single top-left anchor plus regular row/column gaps
  (the default for synthetic-promoted templates).
* ``four_corner`` -- four named corner anchors; cell centres are placed by
  bilinear interpolation inside the quadrilateral (pure geometry, no UI).
"""

from typing import Any, Dict, List, Optional, Tuple

from app.student_recognition.template.coordinates import clamp_norm, is_finite_number
from app.student_recognition.template.template_profile import OptionCell

__all__ = [
    "ANCHOR_MODE_GRID_ORIGIN",
    "ANCHOR_MODE_FOUR_CORNER",
    "CORNER_IDS",
    "AnchorError",
    "parse_question_range",
    "expand_block",
    "bilinear_point",
    "parse_corner_anchors",
]

ANCHOR_MODE_GRID_ORIGIN = "grid_origin"
ANCHOR_MODE_FOUR_CORNER = "four_corner"

# Canonical corner-anchor ids used by four_corner mode.
CORNER_IDS = ("top_left", "top_right", "bottom_right", "bottom_left")


class AnchorError(ValueError):
    """Raised when an anchor configuration is geometrically invalid."""


def parse_question_range(question_range: Any) -> List[int]:
    """Normalize a ``question_range`` into an explicit list of question numbers.

    * ``[start, end]`` (two ints) -> ``range(start, end + 1)`` (continuous).
    * any other list of ints -> used verbatim (explicit / non-contiguous).

    Raises:
        ValueError: If the range is not a list of integers.
    """
    if not isinstance(question_range, (list, tuple)):
        raise ValueError("question_range must be a list/tuple")
    if len(question_range) == 0:
        return []
    if len(question_range) == 2 and all(isinstance(x, int) for x in question_range):
        start, end = question_range
        if start > end:
            raise ValueError("question_range start must be <= end")
        return list(range(start, end + 1))
    result: List[int] = []
    for x in question_range:
        if not isinstance(x, int):
            raise ValueError("question_range entries must be integers")
        result.append(x)
    return result


def _bilinear(corners: Dict[str, Dict[str, float]], u: float, v: float) -> "tuple[float, float]":
    """Bilinearly interpolate a point inside the 4 corner anchors.

    ``u`` is the horizontal fraction (0 at left edge, 1 at right edge) and ``v``
    is the vertical fraction (0 at top edge, 1 at bottom edge).
    """
    tl = corners["top_left"]
    tr = corners["top_right"]
    br = corners["bottom_right"]
    bl = corners["bottom_left"]
    top_x = tl["x"] + (tr["x"] - tl["x"]) * u
    top_y = tl["y"] + (tr["y"] - tl["y"]) * u
    bot_x = bl["x"] + (br["x"] - bl["x"]) * u
    bot_y = bl["y"] + (br["y"] - bl["y"]) * u
    x = top_x + (bot_x - top_x) * v
    y = top_y + (bot_y - top_y) * v
    return (x, y)


def _clamp_roi(roi: Dict[str, float]) -> Dict[str, float]:
    """Clamp a roi so it stays within the normalized [0, 1] box."""
    x = clamp_norm(roi["x"])
    y = clamp_norm(roi["y"])
    w = float(roi["w"])
    h = float(roi["h"])
    if x + w > 1.0:
        w = max(0.0, 1.0 - x)
    if y + h > 1.0:
        h = max(0.0, 1.0 - y)
    return {"x": x, "y": y, "w": w, "h": h}


def expand_block(
    block: Dict[str, Any],
    anchors: Dict[str, Dict[str, Any]],
) -> "tuple[List[OptionCell], Dict[int, Dict[str, float]]]":
    """Deterministically expand a question block into option cells + blank ROIs.

    Args:
        block: A question-block descriptor (see schema doc). Must contain
            ``question_type``, ``options``, ``anchor_id``, ``layout`` and
            ``question_range``; for four_corner mode the referenced anchors must
            include the four ``CORNER_IDS``.
        anchors: Mapping of ``anchor_id -> anchor dict`` for the owning page.

    Returns:
        ``(option_cells, blank_rois)`` where ``option_cells`` is a list of
        :class:`OptionCell` and ``blank_rois`` maps ``question_no -> roi``.

    Raises:
        AnchorError: If the referenced anchor is missing or four_corner corners
            are malformed.
    """
    anchor_mode = block.get("anchor_mode", ANCHOR_MODE_GRID_ORIGIN)
    anchor_id = block.get("anchor_id")
    anchor = anchors.get(anchor_id)
    if anchor is None:
        raise AnchorError(f"anchor {anchor_id!r} not found on page")

    options = list(block.get("options", []) or [])
    question_nos = parse_question_range(block.get("question_range", [1, 1]))
    layout = block.get("layout", {}) or {}
    cell_w = float(layout.get("cell_w", 0.1))
    cell_h = float(layout.get("cell_h", 0.05))
    row_gap = float(layout.get("row_gap", cell_h))
    option_gap = float(layout.get("option_gap", cell_w))

    blank_spec = block.get("blank_roi") or {}
    blank_dx = float(blank_spec.get("dx", 0.0))
    blank_dy = float(blank_spec.get("dy", cell_h))
    blank_w = float(blank_spec.get("w", cell_w))
    blank_h = float(blank_spec.get("h", 0.03))

    cells: List[OptionCell] = []
    blanks: Dict[int, Dict[str, float]] = {}

    if anchor_mode == ANCHOR_MODE_FOUR_CORNER:
        corners = _require_corners(anchors)
        rows = len(question_nos)
        n_opt = len(options)
        for r, q_no in enumerate(question_nos):
            v = (r / (rows - 1)) if rows > 1 else 0.5
            for c, label in enumerate(options):
                u = (c / (n_opt - 1)) if n_opt > 1 else 0.5
                cx, cy = _bilinear(corners, u, v)
                roi = {
                    "x": cx - cell_w / 2.0,
                    "y": cy - cell_h / 2.0,
                    "w": cell_w,
                    "h": cell_h,
                }
                cells.append(
                    OptionCell(
                        question_no=q_no,
                        option_label=label,
                        roi=_clamp_roi(roi),
                    )
                )
            # Blank ROI sits just below the row centre.
            bcx, bcy = _bilinear(corners, 0.5, min(v + cell_h, 1.0))
            blanks[q_no] = _clamp_roi(
                {"x": bcx - blank_w / 2.0, "y": bcy, "w": blank_w, "h": blank_h}
            )
        return cells, blanks

    # Default: grid_origin mode (single top-left anchor + regular gaps).
    anchor_x = float(anchor["x"])
    anchor_y = float(anchor["y"])
    for r, q_no in enumerate(question_nos):
        cell_y = anchor_y + r * row_gap
        for c, label in enumerate(options):
            cell_x = anchor_x + c * option_gap
            roi = {"x": cell_x, "y": cell_y, "w": cell_w, "h": cell_h}
            cells.append(
                OptionCell(question_no=q_no, option_label=label, roi=roi)
            )
        blank_roi = {
            "x": anchor_x + blank_dx,
            "y": cell_y + blank_dy,
            "w": blank_w,
            "h": blank_h,
        }
        blanks[q_no] = blank_roi
    return cells, blanks


def _require_corners(
    anchors: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """Return the four corner anchors, raising AnchorError if incomplete."""
    corners: Dict[str, Dict[str, float]] = {}
    for cid in CORNER_IDS:
        a = anchors.get(cid)
        if a is None:
            raise AnchorError(f"four_corner mode requires anchor {cid!r}")
        if not (
            is_finite_number(a.get("x")) and is_finite_number(a.get("y"))
        ):
            raise AnchorError(f"corner anchor {cid!r} has non-finite coordinates")
        corners[cid] = {"x": float(a["x"]), "y": float(a["y"])}
    return corners


def parse_corner_anchors(
    anchors: List[Dict[str, Any]]
) -> "Optional[Dict[str, Dict[str, float]]]":
    """Parse the four ``CORNER_IDS`` anchors from a list.

    Returns a dict ``{corner_id: {"x": float, "y": float}}`` when all four corner
    anchors are present with finite coordinates, otherwise ``None`` (used by the
    four_corner calibration mode to reject malformed anchor sets).
    """
    by_id = {a.get("anchor_id"): a for a in anchors}
    corners: Dict[str, Dict[str, float]] = {}
    for cid in CORNER_IDS:
        a = by_id.get(cid)
        if a is None:
            return None
        x = a.get("x")
        y = a.get("y")
        if not (is_finite_number(x) and is_finite_number(y)):
            return None
        corners[cid] = {"x": float(x), "y": float(y)}
    return corners
