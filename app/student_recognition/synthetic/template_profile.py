"""Synthetic template geometric profile model.

A ``TemplateProfile`` is the *geometry* of a (synthetic) answer sheet: where the
bubble grid lives, how many questions/options there are, and where the identity
region sits. It deliberately contains **no calibration UI state** -- template
calibration (uploading a blank card and drawing ROIs) is the job of SRE945 and
is explicitly out of scope here (constitution boundary lock).

The schema is intentionally minimal and forward-compatible with SRE945: it only
describes rectangles / grids in pixel coordinates so a future calibrator can
extend or validate it.

Validation failures raise :class:`SyntheticProfileError`, which always carries a
constitutional :class:`~app.student_recognition.errors.error_codes.ErrorCode`
member (constitution §1 B6 -- no free-form reason strings). We reuse the
existing ``TEMPLATE_*`` codes rather than inventing new ones.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.student_recognition.errors.error_codes import ErrorCode

__all__ = [
    "SCHEMA_VERSION",
    "SyntheticProfileError",
    "TemplateProfile",
    "build_default_template",
]

# Bump only when the persisted JSON shape changes incompatibly.
SCHEMA_VERSION: int = 1

# Sensible small canvas so the committed fixtures stay tiny (<= 320x440).
# cell_h is chosen so adjacent bubbles are >12px apart edge-to-edge; this keeps a
# perturbation's drift from pushing a neighbour's fill into another question's
# probe ROI (the truthfulness guard relies on this clearance).
_DEFAULT_CANVAS = {"width": 240, "height": 360}
_DEFAULT_BUBBLE_GRID = {
    "rows": 12,
    "cols": 4,
    "option_labels": ["A", "B", "C", "D"],
    "cell_w": 44,
    "cell_h": 26,
    "origin_x": 36,
    "origin_y": 48,
    "bubble_radius": 6,
}
_DEFAULT_IDENTITY_ROI = {"x": 20, "y": 12, "w": 200, "h": 24}


class SyntheticProfileError(ValueError):
    """Raised when a template profile is invalid.

    Always carries a constitutional :class:`ErrorCode` so callers can branch on
    an enumerated reason instead of parsing a free-form message (constitution
    §1 B6). It subclasses ``ValueError`` so ``except ValueError`` callers still
    catch it.
    """

    def __init__(self, error_code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.error_code: ErrorCode = error_code


@dataclass
class TemplateProfile:
    """Geometry of a synthetic answer sheet.

    Attributes:
        template_id: Stable identifier (e.g. ``"synthetic-v1"``).
        template_version: Integer version of this template.
        canvas: ``{"width": int, "height": int}``.
        bubble_grid: Grid description (see ``_DEFAULT_BUBBLE_GRID``).
        questions: Number of questions (should equal ``bubble_grid.rows``).
        identity_roi: ``{"x", "y", "w", "h"}`` rectangle for the identity region.
    """

    template_id: str
    template_version: int
    canvas: Dict[str, int]
    bubble_grid: Dict[str, Any]
    questions: int
    identity_roi: Dict[str, int]
    schema_version: int = SCHEMA_VERSION

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary of this profile."""
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "canvas": dict(self.canvas),
            "bubble_grid": dict(self.bubble_grid),
            "questions": self.questions,
            "identity_roi": dict(self.identity_roi),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateProfile":
        """Construct a profile from a dict, validating required fields.

        Raises:
            SyntheticProfileError: If a required field is missing or the schema
                version does not match (each case carries a constitutional
                ``ErrorCode``).
        """
        if not isinstance(data, dict):
            raise SyntheticProfileError(
                ErrorCode.TEMPLATE_MISSING, "template profile must be a JSON object"
            )
        if data.get("schema_version") != SCHEMA_VERSION:
            raise SyntheticProfileError(
                ErrorCode.TEMPLATE_VERSION_MISMATCH,
                f"unsupported schema_version: {data.get('schema_version')!r} "
                f"(expected {SCHEMA_VERSION})",
            )
        if "canvas" not in data:
            raise SyntheticProfileError(
                ErrorCode.TEMPLATE_MISSING, "template profile missing 'canvas'"
            )
        if "bubble_grid" not in data:
            raise SyntheticProfileError(
                ErrorCode.TEMPLATE_OPTION_CELL_MISSING,
                "template profile missing 'bubble_grid'",
            )
        if "identity_roi" not in data:
            raise SyntheticProfileError(
                ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING,
                "template profile missing 'identity_roi'",
            )

        canvas = data["canvas"]
        grid = data["bubble_grid"]
        if "rows" not in grid or "cols" not in grid:
            raise SyntheticProfileError(
                ErrorCode.TEMPLATE_OPTION_CELL_MISSING,
                "bubble_grid missing 'rows'/'cols'",
            )

        questions = int(data.get("questions", int(grid["rows"])))
        return cls(
            template_id=str(data.get("template_id", "synthetic-v1")),
            template_version=int(data.get("template_version", 1)),
            canvas={
                "width": int(canvas["width"]),
                "height": int(canvas["height"]),
            },
            bubble_grid={
                "rows": int(grid["rows"]),
                "cols": int(grid["cols"]),
                "option_labels": list(grid.get("option_labels", ["A", "B", "C", "D"])),
                "cell_w": int(grid.get("cell_w", 44)),
                "cell_h": int(grid.get("cell_h", 18)),
                "origin_x": int(grid.get("origin_x", 36)),
                "origin_y": int(grid.get("origin_y", 48)),
                "bubble_radius": int(grid.get("bubble_radius", 6)),
            },
            questions=questions,
            identity_roi={
                "x": int(data["identity_roi"]["x"]),
                "y": int(data["identity_roi"]["y"]),
                "w": int(data["identity_roi"]["w"]),
                "h": int(data["identity_roi"]["h"]),
            },
            schema_version=SCHEMA_VERSION,
        )

    # ------------------------------------------------------------------ #
    # Geometry helpers
    # ------------------------------------------------------------------ #
    def cell_center(self, question_index: int, option_index: int) -> "tuple[int, int]":
        """Return the pixel centre ``(x, y)`` of an option bubble.

        Args:
            question_index: Row index (0-based) of the question.
            option_index: Column index (0-based) of the option.

        Returns:
            ``(x, y)`` centre coordinates in canvas pixels.
        """
        g = self.bubble_grid
        x = int(g["origin_x"]) + int(option_index) * int(g["cell_w"]) + int(g["cell_w"]) // 2
        y = int(g["origin_y"]) + int(question_index) * int(g["cell_h"]) + int(g["cell_h"]) // 2
        return (x, y)

    def option_index(self, label: str) -> int:
        """Return the column index of an option ``label`` (e.g. ``"C"`` -> 2)."""
        labels: List[str] = self.bubble_grid["option_labels"]
        return labels.index(label)


def build_default_template(template_id: str = "synthetic-v1", template_version: int = 1) -> TemplateProfile:
    """Return a small, default synthetic template (12 questions, A-D)."""
    return TemplateProfile(
        template_id=template_id,
        template_version=template_version,
        canvas=dict(_DEFAULT_CANVAS),
        bubble_grid=dict(_DEFAULT_BUBBLE_GRID),
        questions=_DEFAULT_BUBBLE_GRID["rows"],
        identity_roi=dict(_DEFAULT_IDENTITY_ROI),
        schema_version=SCHEMA_VERSION,
    )
