"""Page normalization with a mandatory successful location report."""

from dataclasses import dataclass
from typing import Optional

from .backend import ImageBackend, get_backend
from .image_types import ImageMatrix
from .page_location_report import PageLocationReport


@dataclass(frozen=True)
class NormalizedPageImage:
    image: ImageMatrix
    location: PageLocationReport


def normalize_page(
    image: ImageMatrix,
    report: PageLocationReport,
    width: int,
    height: int,
    backend: Optional[ImageBackend] = None,
) -> NormalizedPageImage:
    if report.status != "page_located":
        raise ValueError("page location must succeed before normalization")
    normalized = (backend or get_backend()).resize(image, width, height)
    return NormalizedPageImage(normalized, report)
