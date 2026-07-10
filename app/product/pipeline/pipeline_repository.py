import json
import sqlite3
import uuid

from app.storage.migrations import utc_now
from app.storage.repositories import ProductRepository

from app.product.review.review_issue_classifier import ReviewIssueType, teacher_message


class PipelineRepository:
    def __init__(self) -> None:
        self.storage = ProductRepository()

    def get_job(self, connection: sqlite3.Connection, job_id: str) -> sqlite3.Row | None:
        return self.storage.one(
            connection,
            "SELECT * FROM capture_jobs WHERE id = ?",
            (job_id,),
        )

    def find_student(
        self,
        connection: sqlite3.Connection,
        class_id: str,
        student_no: str,
        name: str,
    ) -> tuple[sqlite3.Row | None, bool]:
        if student_no:
            row = self.storage.one(
                connection,
                "SELECT * FROM students WHERE class_id = ? AND student_no = ?",
                (class_id, student_no),
            )
            return row, bool(row)
        if name:
            rows = self.storage.all(
                connection,
                "SELECT * FROM students WHERE class_id = ? AND name = ?",
                (class_id, name),
            )
            return (rows[0], False) if len(rows) == 1 else (None, False)
        return None, False

    def identity_already_used(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        student_id: str,
    ) -> bool:
        rows = self.storage.all(
            connection,
            "SELECT provisional_json FROM recognition_drafts WHERE session_id = ?",
            (session_id,),
        )
        for row in rows:
            provisional = json.loads(row["provisional_json"])
            identity = provisional.get("identity") or {}
            if identity.get("student_id") == student_id:
                return True
        return False

    def add_draft(
        self,
        connection: sqlite3.Connection,
        *,
        session_id: str,
        class_id: str,
        job_id: str,
        evidence: dict[str, object],
        provisional: dict[str, object],
        state: str,
    ) -> str:
        draft_id = uuid.uuid4().hex
        now = utc_now()
        self.storage.insert(
            connection,
            "recognition_drafts",
            {
                "id": draft_id,
                "session_id": session_id,
                "class_id": class_id,
                "capture_job_id": job_id,
                "evidence_json": json.dumps(evidence, ensure_ascii=False),
                "provisional_json": json.dumps(provisional, ensure_ascii=False),
                "state": state,
                "created_at": now,
                "updated_at": now,
            },
        )
        return draft_id

    def add_issue(
        self,
        connection: sqlite3.Connection,
        *,
        session_id: str,
        class_id: str,
        job_id: str,
        issue_type: ReviewIssueType,
        question_number: int | None,
        evidence_path: str,
        payload: dict[str, object],
    ) -> str:
        issue_id = uuid.uuid4().hex
        now = utc_now()
        self.storage.insert(
            connection,
            "review_issues",
            {
                "id": issue_id,
                "session_id": session_id,
                "class_id": class_id,
                "capture_job_id": job_id,
                "issue_type": issue_type.value,
                "question_number": question_number,
                "teacher_message": teacher_message(issue_type, question_number),
                "evidence_path": evidence_path,
                "payload_json": json.dumps(payload, ensure_ascii=False),
                "state": "OPEN",
                "created_at": now,
                "updated_at": now,
            },
        )
        return issue_id
