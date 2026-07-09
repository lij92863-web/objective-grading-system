"""Tests for the perturbation transforms and mark-state injections.

Confirms each perturbation produces the *expected, known* effect: a geometric
transform changes pixels, and the mark injections produce the intended fill /
stripe features. These are known transforms, not OMR recognition.
"""

import random
import unittest

from app.student_recognition.synthetic.perturbations import (
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


def _fill_ratio(canvas: Canvas, cx: int, cy: int, r: int) -> float:
    """Fraction of dark pixels (<170) inside the bubble circle."""
    dark = 0
    total = 0
    r2 = r * r
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r2:
                total += 1
                if canvas.get_pixel(cx + dx, cy + dy) < 170:
                    dark += 1
    return dark / total if total else 0.0


def _white_rows(canvas: Canvas, cx: int, cy: int, r: int) -> int:
    """Count rows within the bubble that contain a near-white (>200) pixel."""
    count = 0
    r2 = r * r
    for dy in range(-r, r + 1):
        yy = cy + dy
        if yy < 0 or yy >= canvas.height:
            continue
        has_white = False
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r2 and canvas.get_pixel(cx + dx, yy) > 200:
                has_white = True
                break
        if has_white:
            count += 1
    return count


class TestGeometricPerturbations(unittest.TestCase):
    def test_rotate_small_changes_pixels(self):
        # Off-centre discs so rotation around the canvas centre actually moves
        # them (a disc centred on the rotation pivot would be unchanged).
        c = Canvas(60, 60)
        c.draw_filled_circle(15, 15, 12, 25)
        c.draw_filled_circle(45, 45, 12, 25)
        rng = random.Random(7)
        out = rotate_small(c, rng, max_deg=5)
        self.assertNotEqual(c.to_png_bytes(), out.to_png_bytes())

    def test_shift_changes_pixels_but_keeps_mark(self):
        c = Canvas(60, 60)
        c.draw_filled_circle(30, 30, 12, 25)
        rng = random.Random(3)
        out = shift(c, rng)
        self.assertNotEqual(c.to_png_bytes(), out.to_png_bytes())

    def test_skew_x_changes_pixels(self):
        # Discs at different y so the shear (x' = x - k*y) visibly deforms them;
        # a disc at a single y would just translate by a constant (rounding to 0).
        c = Canvas(60, 60)
        c.draw_filled_circle(15, 15, 12, 25)
        c.draw_filled_circle(45, 45, 12, 25)
        rng = random.Random(11)
        out = skew_x(c, rng, max_skew=0.1)
        self.assertNotEqual(c.to_png_bytes(), out.to_png_bytes())

    def test_box_blur_and_noise_and_contrast_run(self):
        c = Canvas(40, 40)
        c.draw_filled_circle(20, 20, 10, 25)
        rng = random.Random(5)
        self.assertIsInstance(box_blur(c), Canvas)
        self.assertIsInstance(add_gaussian_noise(c, rng), Canvas)
        self.assertIsInstance(contrast(c), Canvas)


class TestMarkInjections(unittest.TestCase):
    def test_inject_multi_mark_fills_two_cells(self):
        c = Canvas(80, 80)
        inject_multi_mark(c, [(20, 20), (60, 60)], 8)
        self.assertGreater(_fill_ratio(c, 20, 20, 8), 0.7)
        self.assertGreater(_fill_ratio(c, 60, 60, 8), 0.7)

    def test_inject_weak_mark_fills_less_than_strong(self):
        strong = Canvas(40, 40)
        strong.draw_filled_circle(20, 20, 8, 25)
        weak = Canvas(40, 40)
        inject_weak_mark(weak, 20, 20, 8)
        self.assertGreater(_fill_ratio(strong, 20, 20, 8), _fill_ratio(weak, 20, 20, 8))
        # weak is still "filled" (above an empty bubble's ~0 ratio).
        self.assertGreater(_fill_ratio(weak, 20, 20, 8), 0.2)

    def test_inject_erased_mark_has_fill_and_stripes(self):
        c = Canvas(60, 60)
        inject_erased_mark(c, 30, 30, 8)
        self.assertGreater(_fill_ratio(c, 30, 30, 8), 0.2, "erased bubble keeps residual fill")
        self.assertGreaterEqual(_white_rows(c, 30, 30, 8), 2, "erased bubble shows erase stripes")


if __name__ == "__main__":
    unittest.main()
