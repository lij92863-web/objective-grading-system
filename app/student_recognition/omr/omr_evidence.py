from dataclasses import dataclass
from typing import Dict, Tuple

from .mark_metrics import MarkMetrics

@dataclass(frozen=True)
class OMREvidence:
    roi_crop_path: str
    image_artifact_hash: str
    template_ref: Dict[str, object]
    question_no: int
    option_labels: Tuple[str, ...]
    metrics: Tuple[MarkMetrics, ...]
