"""Review item model.

A ``ReviewItem`` is the formal unit of human review. Its ``reason_code`` MUST be
an ``ErrorCode`` (constitution B6 / §9 / §10) — never a free-form string. The
item also carries ``evidence`` (path/metrics references, no base64), a
``resolution`` and an append-only ``audit`` log so teacher edits never overwrite
the original recognition result.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.student_recognition.common.timeutil import now_iso
from app.student_recognition.errors.error_codes import ErrorCode


class ReviewStatus(str, Enum):
    """Lifecycle of a single review item (constitution §9.2)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class ReviewItem:
    item_id: str
    reason_code: ErrorCode
    evidence: Dict[str, Any] = field(default_factory=dict)
    resolution: ReviewStatus = ReviewStatus.PENDING
    teacher_note: str = ""
    audit: List[Dict[str, Any]] = field(default_factory=list)
    capture_job_id: str = ""
    question_no: Optional[int] = None
    type: str = "recognition"
    message_for_teacher: str = ""
    candidate_answer: Any = None
    candidate_confidence: float = 0.0
    roi_crop_path: str = ""
    debug_overlay_path: str = ""
    created_at: str = field(default_factory=now_iso)
    resolved_at: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.reason_code, ErrorCode):
            raise TypeError("reason_code must be ErrorCode")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "reason_code": self.reason_code.value,
            "evidence": dict(self.evidence),
            "resolution": self.resolution.value,
            "teacher_note": self.teacher_note,
            "audit": list(self.audit),
            "capture_job_id": self.capture_job_id,
            "question_no": self.question_no,
            "type": self.type,
            "message_for_teacher": self.message_for_teacher,
            "candidate_answer": self.candidate_answer,
            "candidate_confidence": self.candidate_confidence,
            "roi_crop_path": self.roi_crop_path,
            "debug_overlay_path": self.debug_overlay_path,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReviewItem":
        return cls(
            item_id=d["item_id"],
            reason_code=ErrorCode(d["reason_code"]),
            evidence=dict(d.get("evidence", {})),
            resolution=ReviewStatus(d.get("resolution", "pending")),
            teacher_note=d.get("teacher_note", ""),
            audit=list(d.get("audit", [])),
            capture_job_id=d.get("capture_job_id", ""),
            question_no=d.get("question_no"),
            type=d.get("type", "recognition"),
            message_for_teacher=d.get("message_for_teacher", ""),
            candidate_answer=d.get("candidate_answer"),
            candidate_confidence=float(d.get("candidate_confidence", 0.0)),
            roi_crop_path=d.get("roi_crop_path", ""),
            debug_overlay_path=d.get("debug_overlay_path", ""),
            created_at=d.get("created_at", now_iso()),
            resolved_at=d.get("resolved_at"),
        )

    def resolve(self, resolution: ReviewStatus, note: str = "", by: str = "") -> None:
        """Record a teacher resolution without overwriting the original evidence."""
        self.resolution = resolution
        self.teacher_note = note
        self.resolved_at = now_iso()
        self.audit.append(
            {
                "action": "resolve",
                "resolution": resolution.value,
                "note": note,
                "by": by,
                "at": self.resolved_at,
            }
        )

    def is_resolved(self) -> bool:
        return self.resolution == ReviewStatus.RESOLVED
