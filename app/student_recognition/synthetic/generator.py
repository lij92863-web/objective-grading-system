"""Synthetic answer-sheet generator.

:class:`SyntheticSheetGenerator` turns a :class:`TemplateProfile` plus a
:class:`GroundTruth` into a rendered PNG (as bytes) plus the (unchanged) ground
truth. The pipeline:

1. Create a white canvas.
2. Draw faint bubble outlines for every cell (so empty bubbles stay visible but
   are *not* classified as filled by the truthfulness probe).
3. For each answer, paint the mark described by ``mark_type`` at the template
   coordinates: ``strong``/``weak``/``erased`` fill the ``selected`` bubble,
   ``multi`` fills ``selected`` *and* the next option, ``none`` paints nothing.
4. Optionally apply one geometric/noise perturbation.

Determinism: the generator seeds a :class:`random.Random` from ``gt.seed`` (or an
explicit ``rng``), so identical inputs always yield byte-identical PNGs. This is
what lets :mod:`test_synthetic_generator` assert reproducibility and lets the
truthfulness guard trust the rendered output.

The generator is a pure upstream *data factory*: it does not build a
``CaptureJob`` or ``RecognitionDraft`` and never imports grading/OMR code
(constitution §2 B1/B10).
"""

import random
from typing import Callable, Dict, Tuple

from app.student_recognition.synthetic.ground_truth import GroundTruth
from app.student_recognition.synthetic.perturbations import (
    PERTURBATION_NAMES,
    add_gaussian_noise,
    box_blur,
    contrast,
    inject_erased_mark,
    inject_multi_mark,
    inject_weak_mark,
    rotate_small,
    shift,
    skew_x,
)
from app.student_recognition.synthetic.raster import Canvas
from app.student_recognition.synthetic.template_profile import TemplateProfile

__all__ = ["SyntheticSheetGenerator"]

# Maps a perturbation name to its transform. Each takes (canvas, rng).
_PERTURBATIONS: Dict[str, Callable[[Canvas, random.Random], Canvas]] = {
    "skew_x": skew_x,
    "rotate_small": rotate_small,
    "box_blur": box_blur,
    "add_gaussian_noise": add_gaussian_noise,
    "contrast": contrast,
    "shift": shift,
}


class SyntheticSheetGenerator:
    """Render synthetic answer-sheet PNGs from a template + ground truth."""

    @staticmethod
    def build(
        template: TemplateProfile,
        gt: GroundTruth,
        perturbation_name: str = "clean",
        rng: "random.Random | None" = None,
    ) -> Tuple[bytes, GroundTruth]:
        """Render one sheet.

        Args:
            template: Geometry of the sheet.
            gt: Ground truth describing marks / identity / perturbation.
            perturbation_name: One of :data:`PERTURBATION_NAMES` or ``"clean"``.
            rng: Optional seeded RNG; defaults to ``random.Random(gt.seed)``.

        Returns:
            ``(png_bytes, gt)`` -- the encoded PNG and the (echoed) ground truth.

        Raises:
            ValueError: If ``perturbation_name`` is unknown.
        """
        if rng is None:
            rng = random.Random(gt.seed)

        grid = template.bubble_grid
        r = int(grid["bubble_radius"])
        labels = list(grid["option_labels"])
        cols = int(grid["cols"])

        canvas = Canvas(int(template.canvas["width"]), int(template.canvas["height"]))

        # 1) faint outlines for every option bubble
        for q in range(int(grid["rows"])):
            for o in range(cols):
                cx, cy = template.cell_center(q, o)
                canvas.draw_circle_outline(cx, cy, r, 180)

        # 2) paint the marks described by the ground truth
        for ans in gt.answers:
            mark_type = ans.mark_type
            if mark_type == "none" or ans.selected is None:
                continue
            idx = template.option_index(ans.selected)
            cx, cy = template.cell_center(ans.question, idx)
            if mark_type == "strong":
                canvas.draw_filled_circle(cx, cy, r, 25)
            elif mark_type == "weak":
                inject_weak_mark(canvas, cx, cy, r, rng)
            elif mark_type == "erased":
                inject_erased_mark(canvas, cx, cy, r, rng)
            elif mark_type == "multi":
                inject_multi_mark(canvas, [(cx, cy)], r, rng)
                sec_idx = (idx + 1) % cols
                sx, sy = template.cell_center(ans.question, sec_idx)
                canvas.draw_filled_circle(sx, sy, r, 25)

        # 3) optional perturbation (known transform, deterministic via rng)
        if perturbation_name and perturbation_name != "clean":
            fn = _PERTURBATIONS.get(perturbation_name)
            if fn is None:
                raise ValueError(
                    f"unknown perturbation {perturbation_name!r}; "
                    f"expected one of {PERTURBATION_NAMES} or 'clean'"
                )
            # Gentle magnitudes: keep drift (<~8px) well under the inter-bubble
            # clearance so a bubble never bleeds into a neighbour's probe ROI.
            canvas = fn(canvas, rng)

        return canvas.to_png_bytes(), gt
