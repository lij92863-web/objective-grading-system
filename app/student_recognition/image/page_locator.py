"""Fail-closed template-controlled page locator; never reads answer truth."""

from app.student_recognition.errors.error_codes import ErrorCode

from .image_types import ImageMatrix
from .page_location_report import PageLocationReport
from .page_locator_policy import DEFAULT_PAGE_LOCATOR_POLICY, PageLocatorPolicy


def locate_page(
    image: ImageMatrix,
    reference_width: int,
    reference_height: int,
    policy: PageLocatorPolicy = DEFAULT_PAGE_LOCATOR_POLICY,
) -> PageLocationReport:
    mean = sum(image.pixels) / len(image.pixels)
    variance = sum((value - mean) ** 2 for value in image.pixels) / len(image.pixels)
    if variance < policy.min_variance:
        return PageLocationReport(
            "page_location_failed", (), 0.0, (ErrorCode.PAGE_NOT_FOUND,)
        )
    expected_aspect = reference_width / reference_height
    actual_aspect = image.width / image.height
    aspect_error = abs(actual_aspect / expected_aspect - 1.0)
    if aspect_error > policy.max_aspect_ratio_error:
        return PageLocationReport(
            "page_location_failed", (), 0.0,
            (ErrorCode.PAGE_ASPECT_RATIO_INVALID,),
        )
    corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    return PageLocationReport("page_located", corners, 1.0)
