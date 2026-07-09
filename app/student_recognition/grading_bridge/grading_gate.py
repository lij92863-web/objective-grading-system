"""Grading bridge: the dual gates between draft and official grading.

Constitution §2 / §10 / B3 — a ``RecognitionDraft`` MUST pass two gates before
any ``OfficialGradingInput`` is produced:

1. ``RecognitionDraftGate``  — draft has no blocking errors, no unresolved review
   items, and is teacher-confirmed.
2. ``ExamOfficialReportGate`` — all inputs are ``TeacherConfirmedSubmission``,
   no duplicate students, etc.

Even in this skeleton phase the **refuse branches are written dead**: a raw
``RecognitionDraft`` can never become an official input, and an empty / unconfirmed
set can never yield an official report.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.student_recognition.common.timeutil import now_iso
from app.student_recognition.drafts.recognition_draft import RecognitionDraft
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.review.review_item import ReviewStatus
from app.student_recognition.state_model import CONFIRMED_STATES

SCHEMA_VERSION = 1


@dataclass
class TeacherConfirmedSubmission:
    job_id: str
    draft_snapshot: Dict[str, Any]
    confirmed_by: str
    confirmed_at: str
    identity: Optional[Dict[str, Any]] = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "job_id": self.job_id,
            "draft_snapshot": dict(self.draft_snapshot),
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at,
            "identity": self.identity,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TeacherConfirmedSubmission":
        return cls(
            job_id=d["job_id"],
            draft_snapshot=d.get("draft_snapshot", {}),
            confirmed_by=d.get("confirmed_by", ""),
            confirmed_at=d.get("confirmed_at", ""),
            identity=d.get("identity"),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
        )


@dataclass
class OfficialGradingInput:
    exam_id: str
    submissions: List[Dict[str, Any]]
    generated_at: str
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "exam_id": self.exam_id,
            "submissions": list(self.submissions),
            "generated_at": self.generated_at,
        }


@dataclass
class GateResult:
    ok: bool
    code: Optional[ErrorCode]
    payload: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "code": self.code.value if self.code else None}


class RecognitionDraftGate:
    """Gate 1: draft -> TeacherConfirmedSubmission."""

    def try_pass(self, draft: RecognitionDraft) -> GateResult:
        # DEAD REFUSE: a raw RecognitionDraft can only pass if it is
        # teacher-confirmed, has no blocking errors and no unresolved review.
        if not isinstance(draft, RecognitionDraft):
            return GateResult(False, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)
        if draft.status not in CONFIRMED_STATES:
            return GateResult(False, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)
        if draft.blocking_errors:
            return GateResult(False, ErrorCode.GRADING_BLOCKING_ERRORS_EXIST)
        if any(r.resolution != ReviewStatus.RESOLVED for r in draft.review_items):
            return GateResult(False, ErrorCode.GRADING_UNRESOLVED_REVIEW_ITEMS)

        submission = TeacherConfirmedSubmission(
            job_id=draft.job_id,
            draft_snapshot=draft.to_dict(),
            confirmed_by="teacher",
            confirmed_at=now_iso(),
            identity=draft.identity,
        )
        return GateResult(True, None, submission)


class ExamOfficialReportGate:
    """Gate 2: confirmed submissions -> OfficialGradingInput."""

    def try_pass(
        self,
        submissions: List[TeacherConfirmedSubmission],
        exam_id: str = "exam",
    ) -> GateResult:
        # DEAD REFUSE: without confirmed submissions there is no official report.
        if not submissions:
            return GateResult(False, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)
        for sub in submissions:
            # A raw RecognitionDraft must never enter official grading.
            if not isinstance(sub, TeacherConfirmedSubmission):
                return GateResult(False, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)

        student_ids = [
            (s.identity or {}).get("student_id") for s in submissions
        ]
        if any(student_ids.count(x) > 1 for x in student_ids if x):
            return GateResult(False, ErrorCode.GRADING_EXAM_HAS_DUPLICATE_STUDENT)

        official = OfficialGradingInput(
            exam_id=exam_id,
            submissions=[s.to_dict() for s in submissions],
            generated_at=now_iso(),
        )
        return GateResult(True, None, official)

    def refuse_raw_draft(self, draft: RecognitionDraft) -> GateResult:
        # Explicit guard: a RecognitionDraft can never be the input to official grading.
        return GateResult(False, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)
