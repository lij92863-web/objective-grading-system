from dataclasses import dataclass

@dataclass(frozen=True)
class ROIPolicy:
    rounding_epsilon: float = 1e-12

DEFAULT_ROI_POLICY = ROIPolicy()
