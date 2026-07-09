"""R85A: Review queue domain model — clarified status semantics."""
from dataclasses import dataclass, field
from typing import List

# pending = untreated, resolved = can be final, blocked = prevents whole submission
RESOLVED_STATUSES = {"accepted", "corrected", "rejected", "blocked"}


@dataclass
class ReviewQueueItem:
    item_id: str = ""
    draft_id: str = ""
    student_ref: str = ""
    question_id: int = 0
    item_type: str = "choice"  # choice, blank, identity, engine_error, layout, roi
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

    def is_blocking(self) -> bool: return self.severity == "blocking" or self.status == "blocked"
    def is_resolved(self) -> bool: return self.status in RESOLVED_STATUSES
    def is_pending(self) -> bool: return self.status == "pending"
    def resolve_as_accepted(self): self.status = "accepted"
    def resolve_as_rejected(self): self.status = "rejected"
    def resolve_as_blocked(self): self.status = "blocked"
    def resolve_as_corrected(self): self.status = "corrected"


@dataclass
class ResolvedItem:
    item_id: str = ""
    question_id: int = 0
    status: str = ""
    final_answer: str = ""
    is_blocking: bool = False
    is_final: bool = False  # True if answer should go into final output
