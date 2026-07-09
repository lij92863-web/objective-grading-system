"""R81: Review queue domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ReviewQueueItem:
    item_id: str = ""
    draft_id: str = ""
    student_ref: str = ""
    question_id: int = 0
    item_type: str = "choice"
    candidate_answer: str = ""
    confidence: float = 0.0
    reason: str = ""
    source_engine: str = ""
    exception_codes: List[str] = field(default_factory=list)
    severity: str = "review"
    status: str = "pending"
    created_at: str = ""
    resolved_at: str = ""
    corrected_answer: str = ""

    def is_blocking(self) -> bool: return self.severity == "blocking"
    def is_resolved(self) -> bool: return self.status in ("accepted", "corrected", "rejected")
