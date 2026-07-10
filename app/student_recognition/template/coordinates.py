"""Normalized <-> runtime-pixel coordinate conversion (SRE945).

The canonical coordinate system for templates is **normalized** (x, y, w, h in
[0, 1], origin = top-left, unit = ratio). Pixel coordinates are only ever
produced at runtime by :func:`to_runtime_pixels`, using the actual image size.
This keeps the persisted template independent of any specific scan resolution
and free of any image-processing dependency (constitution B4 -- no PIL /
OpenCV / numpy).
"""

import math
from typing import Dict, Union

__all__ = [
    "Number",
    "is_finite_number",
    "to_runtime_pixels",
    "to_runtime_pixel_point",
    "clamp_norm",
]

Number = Union[int, float]

# Tolerance used when checking normalized bounds (accounts for float rounding).
_BOUND_TOLERANCE = 1e-6


def is_finite_number(value: object) -> bool:
    """Return True if *value* is a finite int/float (rejecting NaN/Inf/None/str)."""
    if isinstance(value, bool):
        # bool is a subclass of int; we treat it as non-numeric for coordinates.
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    return False


def to_runtime_pixels(
    norm_roi: Dict[str, Number], width: int, height: int
) -> Dict[str, int]:
    """Map a normalized ROI to runtime pixel integers.

    Args:
        norm_roi: Normalized rectangle ``{"x", "y", "w", "h"}`` with values in
            [0, 1].
        width: Runtime image width in pixels.
        height: Runtime image height in pixels.

    Returns:
        ``{"x", "y", "w", "h"}`` in pixels (``int``), computed as
        ``round(norm * size)``.

    Raises:
        ValueError: If *width* / *height* are not positive finite numbers, or
            *norm_roi* is missing a required key / holds a non-finite number.
    """
    if not is_finite_number(width) or not is_finite_number(height):
        raise ValueError("runtime width/height must be finite numbers")
    if int(width) <= 0 or int(height) <= 0:
        raise ValueError("runtime width/height must be positive")
    for key in ("x", "y", "w", "h"):
        if key not in norm_roi:
            raise ValueError(f"norm_roi missing key {key!r}")
        if not is_finite_number(norm_roi[key]):
            raise ValueError(f"norm_roi[{key}] is not a finite number")
    w = int(width)
    h = int(height)
    return {
        "x": int(round(float(norm_roi["x"]) * w)),
        "y": int(round(float(norm_roi["y"]) * h)),
        "w": int(round(float(norm_roi["w"]) * w)),
        "h": int(round(float(norm_roi["h"]) * h)),
    }


def to_runtime_pixel_point(
    norm_point: Dict[str, Number], width: int, height: int
) -> "tuple[int, int]":
    """Map a normalized point ``{"x", "y"}`` to a runtime pixel ``(x, y)``."""
    if (
        not is_finite_number(width)
        or not is_finite_number(height)
        or int(width) <= 0
        or int(height) <= 0
    ):
        raise ValueError("runtime width/height must be positive finite numbers")
    if "x" not in norm_point or "y" not in norm_point:
        raise ValueError("norm_point must contain 'x' and 'y'")
    if not is_finite_number(norm_point["x"]) or not is_finite_number(norm_point["y"]):
        raise ValueError("norm_point coordinates must be finite numbers")
    return (
        int(round(float(norm_point["x"]) * int(width))),
        int(round(float(norm_point["y"]) * int(height))),
    )


def in_normalized_bounds(roi: Dict[str, Number]) -> bool:
    """Return True if *roi* lies fully within the legal [0, 1] normalized box."""
    for key in ("x", "y", "w", "h"):
        v = roi.get(key)
        if not is_finite_number(v):
            return False
    x = float(roi["x"])
    y = float(roi["y"])
    w = float(roi["w"])
    h = float(roi["h"])
    return (
        x >= -_BOUND_TOLERANCE
        and y >= -_BOUND_TOLERANCE
        and (x + w) <= (1.0 + _BOUND_TOLERANCE)
        and (y + h) <= (1.0 + _BOUND_TOLERANCE)
    )


def clamp_norm(value: Number) -> float:
    """Clamp a normalized value into the legal [0, 1] range."""
    v = float(value)
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v
