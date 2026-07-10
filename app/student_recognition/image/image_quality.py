"""Conservative image-quality analysis."""

import math
from dataclasses import dataclass
from typing import Tuple

from app.student_recognition.errors.error_codes import ErrorCode

from .image_quality_policy import DEFAULT_IMAGE_QUALITY_POLICY, ImageQualityPolicy
from .image_types import ImageMatrix


@dataclass(frozen=True)
class ImageQualityReport:
    status: str
    width: int
    height: int
    brightness_mean: float
    contrast_std: float
    blur_score: float
    dark_saturation_ratio: float
    bright_saturation_ratio: float
    warnings: Tuple[ErrorCode, ...] = ()
    errors: Tuple[ErrorCode, ...] = ()

    def to_dict(self):
        result = dict(self.__dict__)
        result["warnings"] = [code.value for code in self.warnings]
        result["errors"] = [code.value for code in self.errors]
        return result


def assess_image_quality(
    image: ImageMatrix,
    policy: ImageQualityPolicy = DEFAULT_IMAGE_QUALITY_POLICY,
) -> ImageQualityReport:
    values = image.pixels
    pixel_count = len(values)
    brightness_mean = sum(values) / pixel_count
    contrast_std = math.sqrt(
        sum((value - brightness_mean) ** 2 for value in values) / pixel_count
    )
    gradients = [
        abs(image.at(x, y) - image.at(x - 1, y))
        for y in range(image.height)
        for x in range(1, image.width)
    ]
    blur_score = sum(gradients) / len(gradients) if gradients else 0.0
    dark_ratio = sum(value <= policy.dark_cutoff for value in values) / pixel_count
    bright_ratio = sum(value >= policy.bright_cutoff for value in values) / pixel_count

    errors = []
    warnings = []
    if image.width < policy.min_width or image.height < policy.min_height:
        errors.append(ErrorCode.IMG_TOO_SMALL)
    if brightness_mean < policy.min_brightness:
        errors.append(ErrorCode.IMG_TOO_DARK)
    if brightness_mean > policy.max_brightness:
        errors.append(ErrorCode.IMG_TOO_BRIGHT)
    if contrast_std < policy.min_contrast_std:
        warnings.append(ErrorCode.IMG_LOW_CONTRAST)
    if blur_score < policy.min_blur_score:
        warnings.append(ErrorCode.IMG_BLUR_TOO_HIGH)
    if dark_ratio > policy.max_saturation_ratio:
        errors.append(ErrorCode.IMG_TOO_DARK)
    if bright_ratio > policy.max_saturation_ratio:
        warnings.append(ErrorCode.IMG_TOO_BRIGHT)

    status = "quality_failed" if errors else ("needs_review" if warnings else "usable")
    return ImageQualityReport(
        status=status,
        width=image.width,
        height=image.height,
        brightness_mean=brightness_mean,
        contrast_std=contrast_std,
        blur_score=blur_score,
        dark_saturation_ratio=dark_ratio,
        bright_saturation_ratio=bright_ratio,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
    )
