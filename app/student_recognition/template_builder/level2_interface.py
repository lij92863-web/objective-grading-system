"""SRE945 Level-2 (visual) calibrator interface -- declaration only.

This module **defines the interface** a future interactive (GUI / web) calibrator
must implement. It contains **no UI and no implementation** (constitution B5 /
lockdown: no web_app / flask here). It exists so downstream stages (SRE221 /
SRE341) can program against a stable contract, and so the dependency direction is
correct (the interface lives in the template builder, not in any UI layer).

Implementations are expected in a *later* stage and must NOT be added to this
module in the current scope.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class VisualCalibrator(ABC):
    """Abstract contract for an interactive (visual) template calibrator.

    Future implementations (e.g. a web/desktop UI) will subclass this and provide
    a concrete ``start_session`` / ``define_anchor`` / ``draw_roi`` / ``commit``
    flow. This stage declares the surface only.
    """

    @abstractmethod
    def start_session(self, template_id: str, reference_image: Any) -> None:
        """Begin a calibration session for ``template_id`` over a reference image."""
        raise NotImplementedError

    @abstractmethod
    def define_anchor(self, anchor_id: str, normalized_x: float, normalized_y: float) -> None:
        """Record a normalized anchor point placed by the teacher."""
        raise NotImplementedError

    @abstractmethod
    def draw_roi(self, roi: Dict[str, float], label: str) -> None:
        """Record a normalized ROI (e.g. an identity / blank region) drawn by the teacher."""
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> Dict[str, Any]:
        """Finalize the session and return a v2 template dict ready for validation."""
        raise NotImplementedError


__all__ = ["VisualCalibrator"]
