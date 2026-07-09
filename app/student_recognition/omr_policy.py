"""OMR policy stub (constitution §7).

Holds ONLY placeholder threshold constants and a threshold container. The actual
OMR recognition (dark ratio, center density, connected components, border noise)
is implemented in later stages. Per the conservative-OMR rule, thresholds live
here and nowhere else — business functions must read them from this module.
"""

from dataclasses import dataclass
from typing import Dict

# Placeholder thresholds (to be calibrated by SRE945-980 / real OMR stages).
STRONG_MARK_DARK_RATIO = 0.60
WEAK_MARK_DARK_RATIO = 0.30
EMPTY_MARK_DARK_RATIO = 0.08
BORDER_NOISE_MAX = 0.15
MIN_OPTION_COVERAGE = 0.20
MAX_PERSPECTIVE_SKEW = 0.25


@dataclass(frozen=True)
class OMRThreshold:
    """Container for all OMR decision thresholds."""

    strong_mark_dark_ratio: float = STRONG_MARK_DARK_RATIO
    weak_mark_dark_ratio: float = WEAK_MARK_DARK_RATIO
    empty_mark_dark_ratio: float = EMPTY_MARK_DARK_RATIO
    border_noise_max: float = BORDER_NOISE_MAX
    min_option_coverage: float = MIN_OPTION_COVERAGE
    max_perspective_skew: float = MAX_PERSPECTIVE_SKEW

    def as_dict(self) -> Dict[str, float]:
        return dict(self.__dict__)


def default_policy() -> OMRThreshold:
    """Return the default (placeholder) OMR threshold set."""
    return OMRThreshold()
