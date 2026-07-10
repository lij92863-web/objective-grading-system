import json
import sqlite3
import uuid
from enum import Enum

from app.capture.capture_job import CaptureJobState
from app.capture.capture_queue import CaptureQueue
from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now
from app.storage.repositories import ProductRepository
from app.storage.transaction import transaction
from app.infrastructure.loaders.csv_loaders import load_answer_key
from app.product.scoring.manual_score_policy import ManualScorePolicy

from .manual_resolution import TeacherAction
from .review_presenter import PresentedReviewIssue, present_issue, review_sort_key


class ReviewIssueState(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"
    BLOCKED = "BLOCKED"


class ReviewWorkflow:
    def __init__(self, database: LocalDatabase) -> None:
        self.database = database
        self.storage = ProductRepository()
        self.capture = CaptureQueue(database, database.path.parent)
        initialize_database(database)

    def list_issues(
        self,
        session_id: str,
        include_closed: bool = False,
    ) -> list[PresentedReviewIssue]:
        sql = "SELECT * FROM review_issues WHERE session_id = ?"
        parameters: tuple[object, ...] = (session_id,)
        if not include_closed:
            sql += " AND state IN ('OPEN', 'IN_PROGRESS', 'BLOCKED')"
        with self.database.connection() as connection:
            rows = self.storage.all(connection, sql, parameters)
        return sorted((present_issue(row) for row in rows), key=review_sort_key)

    def resolve_identity(
        self,
        issue_id: str,
        *,
        student_no: str = "",
        name: str = "",
        confirm_name: bool = False,
        temporary_reason: str = "",
        actor: str = "teacher",
    ) -> None:
        with transaction(self.database) as connection:
            issue = self._open_issue(connection, issue_id)
            if not issue["issue_type"].startswith("IDENTITY_"):
                raise ValueError("issue is not an identity issue")
            student, action, reason, confirmed, temporary = self._resolve_student(
                connection,
                issue["class_id"],
                student_no.strip(),
                name.strip(),
                confirm_name,
                temporary_reason.strip(),
            )
            self._update_draft_identity(
                connection,
                issue["capture_job_id"],
                student,
                confirmed,
                temporary,
            )
            self._record_resolution(
                connection,
                issue,
                action,
                None,
                reason,
                actor,
                ReviewIssueState.RESOLVED,
            )
            self._close_job_if_ready(connection, issue["capture_job_id"])

    def resolve_answer(
        self,
        issue_id: str,
        action: TeacherAction,
        *,
        manual_score: object = None,
        reason: str,
        actor: str = "teacher",
    ) -> None:
        if action not in {
            TeacherAction.MANUAL_SCORE,
            TeacherAction.MARK_WRONG,
            TeacherAction.MARK_BLANK,
            TeacherAction.WAIVE,
            TeacherAction.EXCLUDE,
        }:
            raise ValueError("unsupported answer resolution")
        if not reason.strip():
            raise ValueError("resolution reason is required")
        with transaction(self.database) as connection:
            issue = self._open_issue(connection, issue_id)
            if issue["issue_type"].startswith("IDENTITY_"):
                raise ValueError("identity issue needs identity resolution")
            answer_key = self._answer_key(connection, issue["session_id"])
            validated_score = ManualScorePolicy.validate(
                answer_key,
                issue["question_number"],
                action,
                manual_score,
            )
            state = (
                ReviewIssueState.WAIVED
                if action in {TeacherAction.WAIVE, TeacherAction.EXCLUDE}
                else ReviewIssueState.RESOLVED
            )
            self._record_resolution(
                connection,
                issue,
                action,
                validated_score,
                reason.strip(),
                actor,
                state,
            )
            if action is TeacherAction.EXCLUDE:
                self.capture.update_state(
                    connection,
                    issue["capture_job_id"],
                    CaptureJobState.EXCLUDED,
                )
            else:
                self._close_job_if_ready(connection, issue["capture_job_id"])

    def exclude_capture_from_identity_issue(
        self,
        issue_id: str,
        *,
        reason: str,
        actor: str = "teacher",
    ) -> None:
        reason = reason.strip()
        actor = actor.strip()
        if not reason:
            raise ValueError("capture exclusion reason is required")
        if not actor:
            raise ValueError("capture exclusion actor is required")
        with transaction(self.database) as connection:
            issue = self._open_issue(connection, issue_id)
            if not issue["issue_type"].startswith("IDENTITY_"):
                raise ValueError("capture exclusion requires an identity issue")
            session = self.storage.one(
                connection,
                "SELECT state FROM exam_sessions WHERE session_id = ?",
                (issue["session_id"],),
            )
            if session is None:
                raise ValueError("session does not exist")
            if session["state"] in {"FINALIZED", "ARCHIVED"}:
                raise ValueError("finalized or archived session is read-only")
            published = self.storage.one(
                connection,
                "SELECT COUNT(*) AS count FROM final_scores WHERE session_id = ?",
                (issue["session_id"],),
            )["count"]
            if published:
                raise ValueError("capture already participates in official scores")
            job = self.storage.one(
                connection,
                "SELECT * FROM capture_jobs WHERE id = ? AND session_id = ?",
                (issue["capture_job_id"], issue["session_id"]),
            )
            if job is None:
                raise ValueError("capture job does not exist in this session")
            if job["state"] == CaptureJobState.EXCLUDED.value:
                raise ValueError("capture job is already excluded")
            open_issues = self.storage.all(
                connection,
                """
                SELECT * FROM review_issues
                WHERE capture_job_id = ?
                  AND state IN ('OPEN', 'IN_PROGRESS', 'BLOCKED')
                ORDER BY created_at, id
                """,
                (issue["capture_job_id"],),
            )
            if not open_issues:
                raise ValueError("capture job has no open review issue")
            for open_issue in open_issues:
                self._record_resolution(
                    connection,
                    open_issue,
                    TeacherAction.EXCLUDE_CAPTURE,
                    None,
                    reason,
                    actor,
                    ReviewIssueState.WAIVED,
                )
            self.capture.update_state(
                connection,
                issue["capture_job_id"],
                CaptureJobState.EXCLUDED,
            )
            now = utc_now()
            self.storage.insert(
                connection,
                "audit_events",
                {
                    "id": uuid.uuid4().hex,
                    "session_id": issue["session_id"],
                    "class_id": issue["class_id"],
                    "entity_type": "capture_job",
                    "entity_id": issue["capture_job_id"],
                    "action": TeacherAction.EXCLUDE_CAPTURE.value,
                    "actor": actor,
                    "payload_json": json.dumps(
                        {
                            "reason": reason,
                            "source_issue_id": issue_id,
                            "closed_issue_ids": [row["id"] for row in open_issues],
                        },
                        ensure_ascii=False,
                    ),
                    "state": "RECORDED",
                    "created_at": now,
                    "updated_at": now,
                },
            )

    def _resolve_student(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        student_no: str,
        name: str,
        confirm_name: bool,
        temporary_reason: str,
    ) -> tuple[sqlite3.Row, TeacherAction, str, bool, bool]:
        if student_no:
            student = self.storage.one(
                connection,
                "SELECT * FROM students WHERE class_id = ? AND student_no = ?",
                (class_id, student_no),
            )
            if student is not None:
                if name and name != student["name"]:
                    raise ValueError("student number and name conflict")
                return student, TeacherAction.BIND_IDENTITY, "学号精确匹配", True, False
        if name:
            matches = self.storage.all(
                connection,
                "SELECT * FROM students WHERE class_id = ? AND name = ?",
                (class_id, name),
            )
            if len(matches) > 1:
                raise ValueError("name is duplicated in this class")
            if len(matches) == 1:
                if not confirm_name:
                    raise ValueError("unique name match requires teacher confirmation")
                return matches[0], TeacherAction.BIND_IDENTITY, "教师确认唯一同名匹配", True, False
        if not temporary_reason:
            raise ValueError("temporary student requires a reason")
        now = utc_now()
        temporary_id = uuid.uuid4().hex
        temporary_no = student_no or f"TEMP-{temporary_id[:8]}"
        temporary_name = name or "临时学生"
        self.storage.insert(
            connection,
            "students",
            {
                "id": temporary_id,
                "class_id": class_id,
                "student_no": temporary_no,
                "name": temporary_name,
                "aliases": "[]",
                "state": "TEMPORARY_UNCONFIRMED",
                "created_at": now,
                "updated_at": now,
            },
        )
        student = self.storage.one(
            connection,
            "SELECT * FROM students WHERE id = ?",
            (temporary_id,),
        )
        return (
            student,
            TeacherAction.CREATE_TEMPORARY_STUDENT,
            temporary_reason,
            False,
            True,
        )

    def _update_draft_identity(
        self,
        connection: sqlite3.Connection,
        capture_job_id: str,
        student: sqlite3.Row,
        confirmed: bool,
        temporary: bool,
    ) -> None:
        draft = self.storage.one(
            connection,
            "SELECT * FROM recognition_drafts WHERE capture_job_id = ?",
            (capture_job_id,),
        )
        payload = json.loads(draft["provisional_json"])
        payload["identity"] = {
            "student_id": student["id"],
            "student_no": student["student_no"],
            "name": student["name"],
            "confirmed": confirmed,
            "temporary": temporary,
        }
        connection.execute(
            """
            UPDATE recognition_drafts
            SET provisional_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(payload, ensure_ascii=False), utc_now(), draft["id"]),
        )

    def _record_resolution(
        self,
        connection: sqlite3.Connection,
        issue: sqlite3.Row,
        action: TeacherAction,
        manual_score: float | None,
        reason: str,
        actor: str,
        state: ReviewIssueState,
    ) -> None:
        now = utc_now()
        resolution_id = uuid.uuid4().hex
        self.storage.insert(
            connection,
            "review_resolutions",
            {
                "id": resolution_id,
                "session_id": issue["session_id"],
                "class_id": issue["class_id"],
                "issue_id": issue["id"],
                "teacher_action": action.value,
                "manual_score": manual_score,
                "reason": reason,
                "original_evidence_path": issue["evidence_path"],
                "actor": actor,
                "state": "RECORDED",
                "created_at": now,
                "updated_at": now,
            },
        )
        connection.execute(
            "UPDATE review_issues SET state = ?, updated_at = ? WHERE id = ?",
            (state.value, now, issue["id"]),
        )
        self.storage.insert(
            connection,
            "audit_events",
            {
                "id": uuid.uuid4().hex,
                "session_id": issue["session_id"],
                "class_id": issue["class_id"],
                "entity_type": "review_issue",
                "entity_id": issue["id"],
                "action": action.value,
                "actor": actor,
                "payload_json": json.dumps(
                    {"reason": reason, "manual_score": manual_score},
                    ensure_ascii=False,
                ),
                "state": "RECORDED",
                "created_at": now,
                "updated_at": now,
            },
        )

    def _close_job_if_ready(
        self,
        connection: sqlite3.Connection,
        capture_job_id: str,
    ) -> None:
        open_count = self.storage.one(
            connection,
            """
            SELECT COUNT(*) AS count FROM review_issues
            WHERE capture_job_id = ? AND state IN ('OPEN', 'IN_PROGRESS', 'BLOCKED')
            """,
            (capture_job_id,),
        )["count"]
        if open_count == 0:
            self.capture.update_state(
                connection,
                capture_job_id,
                CaptureJobState.CONFIRMED,
            )

    def _open_issue(
        self,
        connection: sqlite3.Connection,
        issue_id: str,
    ) -> sqlite3.Row:
        issue = self.storage.one(
            connection,
            "SELECT * FROM review_issues WHERE id = ?",
            (issue_id,),
        )
        if issue is None:
            raise ValueError("review issue does not exist")
        if issue["state"] not in {"OPEN", "IN_PROGRESS", "BLOCKED"}:
            raise ValueError("review issue is already closed")
        return issue

    def _answer_key(self, connection: sqlite3.Connection, session_id: str):
        row = self.storage.one(
            connection,
            """
            SELECT a.stored_path
            FROM exam_sessions s
            JOIN exam_assets a ON a.id = s.answer_key_asset_id
            WHERE s.session_id = ? AND a.state = 'VALID'
            """,
            (session_id,),
        )
        if row is None:
            raise ValueError("canonical answer key is unavailable")
        return load_answer_key(row["stored_path"])
