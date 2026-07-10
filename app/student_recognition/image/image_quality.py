import math
from dataclasses import dataclass
from typing import Tuple
from app.student_recognition.errors.error_codes import ErrorCode
from .image_types import ImageMatrix
from .image_quality_policy import DEFAULT_IMAGE_QUALITY_POLICY,ImageQualityPolicy

@dataclass(frozen=True)
class ImageQualityReport:
    status:str; width:int; height:int; brightness_mean:float; contrast_std:float; blur_score:float
    dark_saturation_ratio:float; bright_saturation_ratio:float; warnings:Tuple[ErrorCode,...]=(); errors:Tuple[ErrorCode,...]=()
    def to_dict(self):
        d=dict(self.__dict__); d["warnings"]=[x.value for x in self.warnings]; d["errors"]=[x.value for x in self.errors]; return d

def assess_image_quality(image:ImageMatrix,policy:ImageQualityPolicy=DEFAULT_IMAGE_QUALITY_POLICY)->ImageQualityReport:
    values=image.pixels; n=len(values); mean=sum(values)/n; std=math.sqrt(sum((v-mean)**2 for v in values)/n)
    gradients=[abs(image.at(x,y)-image.at(x-1,y)) for y in range(image.height) for x in range(1,image.width)]
    blur=sum(gradients)/len(gradients) if gradients else 0
    dark=sum(v<=policy.dark_cutoff for v in values)/n; bright=sum(v>=policy.bright_cutoff for v in values)/n
    errors=[]; warnings=[]
    if image.width<policy.min_width or image.height<policy.min_height: errors.append(ErrorCode.IMG_TOO_SMALL)
    if mean<policy.min_brightness: errors.append(ErrorCode.IMG_TOO_DARK)
    if mean>policy.max_brightness: errors.append(ErrorCode.IMG_TOO_BRIGHT)
    if std<policy.min_contrast_std: warnings.append(ErrorCode.IMG_LOW_CONTRAST)
    if blur<policy.min_blur_score: warnings.append(ErrorCode.IMG_BLUR_TOO_HIGH)
    if dark>policy.max_saturation_ratio: errors.append(ErrorCode.IMG_TOO_DARK)
    if bright>policy.max_saturation_ratio: warnings.append(ErrorCode.IMG_TOO_BRIGHT)
    status="quality_failed" if errors else ("needs_review" if warnings else "usable")
    return ImageQualityReport(status,image.width,image.height,mean,std,blur,dark,bright,tuple(dict.fromkeys(warnings)),tuple(dict.fromkeys(errors)))
