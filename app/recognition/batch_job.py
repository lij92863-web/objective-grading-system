"""R89: Batch recognition job model."""
from dataclasses import dataclass, field
from typing import List

VALID_TRANSITIONS = {"created": {"running", "cancelled"},
    "running": {"completed", "completed_with_review", "failed", "blocked", "cancelled"},
    "completed": set(), "completed_with_review": set(), "failed": set(), "blocked": set(), "cancelled": set()}


@dataclass
class RecognitionBatchJob:
    job_id: str = ""
    exam_id: str = ""
    template_id: str = ""
    image_asset_ids: List[str] = field(default_factory=list)
    status: str = "created"
    created_at: str = ""
    summary: dict = field(default_factory=dict)

    def transition(self, new_status: str) -> bool:
        if new_status not in VALID_TRANSITIONS.get(self.status, set()):
            return False
        self.status = new_status
        return True
