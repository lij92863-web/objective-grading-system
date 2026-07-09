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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "reason_code": self.reason_code.value,
            "evidence": dict(self.evidence),
            "resolution": self.resolution.value,
            "teacher_note": self.teacher_note,
            "audit": list(self.audit),
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
        )

    def resolve(self, resolution: ReviewStatus, note: str = "", by: str = "") -> None:
        """Record a teacher resolution without overwriting the original evidence."""
        self.resolution = resolution
        self.teacher_note = note
        self.audit.append(
            {
                "action": "resolve",
                "resolution": resolution.value,
                "note": note,
                "by": by,
                "at": now_iso(),
            }
        )

    def is_resolved(self) -> bool:
        return self.resolution == ReviewStatus.RESOLVED
