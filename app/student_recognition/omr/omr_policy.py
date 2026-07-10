from dataclasses import dataclass
@dataclass(frozen=True)
class OMRPolicy:
    dark_pixel_cutoff:int=180; strong_dark_ratio:float=.55; weak_dark_ratio:float=.15
    selected_threshold:float=.55; weak_threshold:float=.25; single_choice_margin:float=.20
    border_noise_limit:float=.55; erasure_threshold:float=.32; ambiguous_low:float=.25; ambiguous_high:float=.55
DEFAULT_OMR_POLICY=OMRPolicy()
