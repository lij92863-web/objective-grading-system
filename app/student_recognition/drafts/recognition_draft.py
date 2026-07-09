"""Recognition draft model (constitution §2 / B2).

A ``RecognitionDraft`` holds *candidates* (OMR answers, identity) produced by the
recognition stage. It is a candidate, never a grade: ``blocking_errors`` use
``ErrorCode`` and ``review_items`` carry ``ErrorCode`` reason codes. The draft
MUST NOT write ``submissions.csv`` or generate an official report.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.student_recognition.common.timeutil import now_iso
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.review.review_item import ReviewItem
from app.student_recognition.state_model import State


@dataclass
class RecognitionDraft:
    job_id: str
    status: State = State.DRAFT_CREATED
    candidates: Dict[str, Any] = field(default_factory=dict)  # q_id -> candidate value
    identity: Optional[Dict[str, Any]] = None  # serialized IdentityCandidate
    blocking_errors: List[ErrorCode] = field(default_factory=list)
    review_items: List[ReviewItem] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)
    schema_version: int = 1

    def append_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self.events.append(
            {"type": event_type, "payload": payload or {}, "at": now_iso()}
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "job_id": self.job_id,
            "status": self.status.value,
            "candidates": dict(self.candidates),
            "identity": self.identity,
            "blocking_errors": [c.value for c in self.blocking_errors],
            "review_items": [r.to_dict() for r in self.review_items],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": list(self.events),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RecognitionDraft":
        return cls(
            job_id=d["job_id"],
            status=State(d["status"]),
            candidates=dict(d.get("candidates", {})),
            identity=d.get("identity"),
            blocking_errors=[ErrorCode(v) for v in d.get("blocking_errors", [])],
            review_items=[ReviewItem.from_dict(r) for r in d.get("review_items", [])],
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            events=list(d.get("events", [])),
            schema_version=d.get("schema_version", 1),
        )
