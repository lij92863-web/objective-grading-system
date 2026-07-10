from dataclasses import dataclass
@dataclass(frozen=True)
class ImageQualityPolicy:
    min_width:int=100; min_height:int=100; min_brightness:float=35; max_brightness:float=245
    min_contrast_std:float=12; min_blur_score:float=18; dark_cutoff:int=15; bright_cutoff:int=245; max_saturation_ratio:float=.85
DEFAULT_IMAGE_QUALITY_POLICY=ImageQualityPolicy()
