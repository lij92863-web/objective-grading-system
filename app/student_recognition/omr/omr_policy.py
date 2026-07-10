from dataclasses import dataclass
@dataclass(frozen=True)
class OMRPolicy:
    dark_pixel_cutoff:int=180; strong_dark_ratio:float=.08; strong_center_density:float=.30; weak_dark_ratio:float=.02
    selected_threshold:float=.18; weak_threshold:float=.08; single_choice_margin:float=.10
    border_noise_limit:float=.55; erasure_threshold:float=.08; ambiguous_low:float=.08; ambiguous_high:float=.18
    dark_ratio_weight:float=.45; center_density_weight:float=.35
    component_weight:float=.20; border_noise_weight:float=.25
DEFAULT_OMR_POLICY=OMRPolicy()
