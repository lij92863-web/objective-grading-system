"""Synthetic perturbations: image transforms and mark-state injections.

All functions are pure standard library (constitution §1 B4). Two families:

1. **Geometric / noise transforms** (``skew_x``, ``rotate_small``, ``box_blur``,
   ``add_gaussian_noise``, ``contrast``, ``shift``): each takes a :class:`Canvas`
   and a seeded :class:`random.Random` and returns a *new* canvas. Because the
   ``Random`` instance is seeded from the sheet's ``seed``, applying the same
   perturbation to the same input is deterministic.

2. **Mark-state injections** (``inject_weak_mark``, ``inject_multi_mark``,
   ``inject_erased_mark``): these paint a *known* mark onto a bubble so the
   generator's output stays verifiable. The transform is fully described (we know
   exactly which bubble was weakened / doubled / erased), which is precisely what
   makes the ground truth trustworthy -- this is **not** OMR and does not consult
   ``omr_policy`` (constitution boundary lock).

Every perturbation is a *known* transformation; nothing here attempts recognition.
"""

import math
import random
from typing import List, Optional, Sequence, Tuple

from app.student_recognition.synthetic.raster import Canvas

__all__ = [
    "skew_x",
    "rotate_small",
    "box_blur",
    "add_gaussian_noise",
    "contrast",
    "shift",
    "inject_weak_mark",
    "inject_multi_mark",
    "inject_erased_mark",
    "PERTURBATION_NAMES",
]

# Names of the geometric/noise perturbations understood by the generator.
PERTURBATION_NAMES: "tuple[str, ...]" = (
    "skew_x",
    "rotate_small",
    "box_blur",
    "add_gaussian_noise",
    "contrast",
    "shift",
)

_DARK = 25          # intensity of a solid graphite fill
_ERASE_WHITE = 245  # intensity of an erasure stripe


def _sample(src: Canvas, x: float, y: float, background: int = 255) -> int:
    """Nearest-neighbour sample of ``src`` at float coords; out-of-bounds -> background."""
    xi = int(round(x))
    yi = int(round(y))
    if 0 <= xi < src.width and 0 <= yi < src.height:
        return src.get_pixel(xi, yi)
    return background


# ---------------------------------------------------------------------- #
# Geometric / noise transforms
# ---------------------------------------------------------------------- #
def skew_x(src: Canvas, rng: random.Random, max_skew: float = 0.015) -> Canvas:
    """Horizontal shear by a small random factor (x' = x - k*y)."""
    k = rng.uniform(-max_skew, max_skew)
    out = Canvas(src.width, src.height)
    for y in range(src.height):
        for x in range(src.width):
            out.set_pixel(x, y, _sample(src, x - k * y, y))
    return out


def rotate_small(src: Canvas, rng: random.Random, max_deg: float = 2.0) -> Canvas:
    """Rotate the whole sheet by a small random angle (degrees)."""
    angle = math.radians(rng.uniform(-max_deg, max_deg))
    cx = src.width / 2.0
    cy = src.height / 2.0
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    out = Canvas(src.width, src.height)
    for y in range(src.height):
        for x in range(src.width):
            dx = x - cx
            dy = y - cy
            sx = dx * cos_a + dy * sin_a + cx
            sy = -dx * sin_a + dy * cos_a + cy
            out.set_pixel(x, y, _sample(src, sx, sy))
    return out


def box_blur(src: Canvas, rng: Optional[random.Random] = None, radius: int = 1) -> Canvas:
    """Simple box blur (averages a (2r+1)x(2r+1) neighbourhood)."""
    out = Canvas(src.width, src.height)
    for y in range(src.height):
        for x in range(src.width):
            total = 0
            n = 0
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    xi = x + dx
                    yi = y + dy
                    if 0 <= xi < src.width and 0 <= yi < src.height:
                        total += src.get_pixel(xi, yi)
                        n += 1
            out.set_pixel(x, y, int(total / n) if n else src.get_pixel(x, y))
    return out


def add_gaussian_noise(src: Canvas, rng: random.Random, sigma: float = 12.0) -> Canvas:
    """Add zero-mean Gaussian noise (clamped to 0..255)."""
    out = Canvas(src.width, src.height)
    for y in range(src.height):
        for x in range(src.width):
            v = src.get_pixel(x, y) + rng.gauss(0.0, sigma)
            out.set_pixel(x, y, max(0, min(255, int(v))))
    return out


def contrast(src: Canvas, rng: Optional[random.Random] = None, factor: float = 1.15) -> Canvas:
    """Adjust contrast around the mid-grey 128 anchor."""
    out = Canvas(src.width, src.height)
    for y in range(src.height):
        for x in range(src.width):
            v = 128 + (src.get_pixel(x, y) - 128) * factor
            out.set_pixel(x, y, max(0, min(255, int(v))))
    return out


def shift(src: Canvas, rng: random.Random, max_shift: int = 5) -> Canvas:
    """Translate the sheet by a small random offset."""
    dx = rng.randint(-max_shift, max_shift)
    dy = rng.randint(-max_shift, max_shift)
    out = Canvas(src.width, src.height)
    for y in range(src.height):
        for x in range(src.width):
            out.set_pixel(x, y, _sample(src, x - dx, y - dy))
    return out


# ---------------------------------------------------------------------- #
# Mark-state injections (paint a *known* mark)
# ---------------------------------------------------------------------- #
def inject_weak_mark(canvas: Canvas, cx: int, cy: int, r: int, rng: Optional[random.Random] = None) -> Canvas:
    """Paint a *weak* (partial) fill: a smaller solid disc reduces the dark ratio.

    The reduced radius (rather than a lighter grey) is what lowers the fill ratio
    the truthfulness guard measures, so it reads as "weak" and not "none".
    """
    canvas.draw_filled_circle(cx, cy, max(1, r - 2), _DARK)
    return canvas


def inject_multi_mark(canvas: Canvas, centers: Sequence[Tuple[int, int]], r: int, rng: Optional[random.Random] = None) -> Canvas:
    """Paint a *multi* mark: fill every supplied bubble centre strongly."""
    for (cx, cy) in centers:
        canvas.draw_filled_circle(cx, cy, r, _DARK)
    return canvas


def inject_erased_mark(canvas: Canvas, cx: int, cy: int, r: int, rng: Optional[random.Random] = None) -> Canvas:
    """Paint a *strong* fill then overlay periodic white erase stripes.

    The resulting bubble has both fill (residual graphite) and horizontal white
    stripes -- a pattern the truthfulness guard detects as "erased".
    """
    canvas.draw_filled_circle(cx, cy, r, _DARK)
    stripe_gap = max(2, r // 2)
    r2 = r * r
    for yy in range(cy - r, cy + r + 1, stripe_gap):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r2:
                canvas.set_pixel(xx, yy, _ERASE_WHITE)
    return canvas
