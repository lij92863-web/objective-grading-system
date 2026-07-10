import dataclasses
import json
from collections import Counter
from typing import Iterable

from app.domain.grading import Submission
from app.storage.repositories import ProductRepository
from app.student_recognition.grading_bridge.grading_gate import (
    TeacherConfirmedSubmission,
)


@dataclasses.dataclass(frozen=True)
class ConfirmedSubmissionBuild:
    submissions: tuple[TeacherConfirmedSubmission, ...]
    blockers: tuple[str, ...]


class ConfirmedSubmissionBuilder:
    """Build the grading bridge input exclusively from persisted product facts."""

    def __init__(self) -> None:
        self.storage = ProductRepository()

    def build(
        self,
        connection,
        session_id: str,
        grading_submissions: Iterable[Submission],
    ) -> ConfirmedSubmissionBuild:
        blockers: list[str] = []
        submission_by_student, submission_blockers = self._submission_index(
            grading_submissions
        )
        blockers.extend(submission_blockers)
        confirmation = self._confirmation(connection, session_id)
        if confirmation is None:
            blockers.append("teacher_confirmation_audit_missing")
        all_jobs, drafts_by_job = self._jobs_and_drafts(connection, session_id)
        jobs = [job for job in all_jobs if job["state"] != "EXCLUDED"]
        known_job_ids = {str(job["id"]) for job in all_jobs}
        blockers.extend(
            f"confirmed_snapshot_job_missing:{job_id}"
            for job_id in drafts_by_job.keys() - known_job_ids
        )

        confirmed: list[TeacherConfirmedSubmission] = []
        matched_students: set[str] = set()
        for job in jobs:
            built, student_id, item_blockers = self._build_job(
                connection,
                session_id,
                job,
                drafts_by_job,
                submission_by_student,
                matched_students,
                confirmation,
            )
            blockers.extend(item_blockers)
            if built is not None:
                confirmed.append(built)
                matched_students.add(student_id)

        for student_id in submission_by_student.keys() - matched_students:
            blockers.append(f"confirmed_snapshot_job_missing:{student_id}")
        return ConfirmedSubmissionBuild(
            tuple(confirmed),
            tuple(dict.fromkeys(blockers)),
        )

    @staticmethod
    def _submission_index(grading_submissions):
        submissions = list(grading_submissions)
        counts = Counter(item.student_id for item in submissions)
        index = {
            item.student_id: item
            for item in submissions
            if counts[item.student_id] == 1
        }
        blockers = [
            f"confirmed_submission_duplicate:{student_id}"
            for student_id, count in counts.items()
            if count > 1
        ]
        return index, blockers

    def _confirmation(self, connection, session_id):
        return self.storage.one(
            connection,
            """
            SELECT actor, created_at FROM audit_events
            WHERE session_id = ? AND entity_type = 'exam_session'
              AND entity_id = ? AND action = 'TEACHER_CONFIRM'
              AND state = 'RECORDED'
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (session_id, session_id),
        )

    def _jobs_and_drafts(self, connection, session_id):
        jobs = self.storage.all(
            connection,
            "SELECT * FROM capture_jobs WHERE session_id = ? ORDER BY created_at, id",
            (session_id,),
        )
        drafts = self.storage.all(
            connection,
            "SELECT * FROM recognition_drafts WHERE session_id = ? ORDER BY created_at, id",
            (session_id,),
        )
        drafts_by_job = {}
        for draft in drafts:
            drafts_by_job.setdefault(str(draft["capture_job_id"]), []).append(draft)
        return jobs, drafts_by_job

    def _build_job(
        self,
        connection,
        session_id,
        job,
        drafts_by_job,
        submission_by_student,
        matched_students,
        confirmation,
    ):
        job_id = str(job["id"])
        job_drafts = drafts_by_job.get(job_id, [])
        if not job_drafts:
            return None, "", [f"confirmed_snapshot_draft_missing:{job_id}"]
        if len(job_drafts) != 1:
            return None, "", [f"confirmed_snapshot_draft_duplicate:{job_id}"]
        draft = job_drafts[0]
        try:
            provisional = json.loads(draft["provisional_json"])
            evidence = json.loads(draft["evidence_json"])
        except (TypeError, ValueError, json.JSONDecodeError):
            return None, "", [f"confirmed_snapshot_json_invalid:{job_id}"]
        identity = provisional.get("identity") or {}
        student_id = str(identity.get("student_id") or "")
        if not student_id:
            return None, "", [f"confirmed_snapshot_identity_missing:{job_id}"]
        if student_id not in submission_by_student:
            blocker = f"confirmed_snapshot_submission_missing:{job_id}:{student_id}"
            return None, student_id, [blocker]
        if student_id in matched_students:
            return None, student_id, [f"confirmed_snapshot_student_duplicate:{student_id}"]
        review_items, blocking_errors, blockers = self._review_snapshot(
            connection, session_id, job_id
        )
        snapshot = {
            "source_draft_id": str(draft["id"]),
            "capture_job_id": job_id,
            "capture_job_state": str(job["state"]),
            "draft_state": str(draft["state"]),
            "evidence": evidence,
            "provisional": provisional,
            "blocking_errors": blocking_errors,
            "review_items": review_items,
        }
        built = TeacherConfirmedSubmission(
            job_id=job_id,
            draft_snapshot=snapshot,
            confirmed_by=str(confirmation["actor"]) if confirmation else "",
            confirmed_at=str(confirmation["created_at"]) if confirmation else "",
            identity=dict(identity),
        )
        return built, student_id, blockers

    def _review_snapshot(self, connection, session_id, job_id):
        issues = self.storage.all(
            connection,
            """
            SELECT * FROM review_issues
            WHERE session_id = ? AND capture_job_id = ?
            ORDER BY created_at, id
            """,
            (session_id, job_id),
        )
        review_items, blocking_errors, blockers = [], [], []
        for issue in issues:
            resolutions = self.storage.all(
                connection,
                """
                SELECT * FROM review_resolutions
                WHERE session_id = ? AND issue_id = ?
                ORDER BY created_at, id
                """,
                (session_id, issue["id"]),
            )
            is_open = issue["state"] in {"OPEN", "IN_PROGRESS", "BLOCKED"}
            if is_open:
                blocking_errors.append(str(issue["issue_type"]))
            if not is_open and not resolutions:
                blockers.append(f"confirmed_snapshot_resolution_missing:{issue['id']}")
            review_items.append(self._review_item(issue, resolutions, is_open))
        return review_items, blocking_errors, blockers

    def _review_item(self, issue, resolutions, is_open):
        return {
            "issue_id": str(issue["id"]),
            "issue_type": str(issue["issue_type"]),
            "question_number": issue["question_number"],
            "issue_state": str(issue["state"]),
            "evidence_path": str(issue["evidence_path"]),
            "resolution": "unresolved" if is_open else "resolved",
            "review_history": [self._resolution_snapshot(row) for row in resolutions],
        }

    @staticmethod
    def _resolution_snapshot(row) -> dict[str, object]:
        return {
            "resolution_id": str(row["id"]),
            "teacher_action": str(row["teacher_action"]),
            "manual_score": row["manual_score"],
            "reason": str(row["reason"]),
            "original_evidence_path": str(row["original_evidence_path"]),
            "actor": str(row["actor"]),
            "state": str(row["state"]),
            "created_at": str(row["created_at"]),
        }
