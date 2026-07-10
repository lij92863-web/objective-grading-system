import dataclasses
import json
from collections import Counter
from enum import Enum
from pathlib import Path

from app.domain.grading import AnswerKey, Submission, normalize_answer, run_grading_precheck
from app.infrastructure.loaders.csv_loaders import load_answer_key
from app.storage.local_db import LocalDatabase
from app.storage.repositories import ProductRepository
from app.student_recognition.grading_bridge.grading_gate import (
    ExamOfficialReportGate,
    TeacherConfirmedSubmission,
)
from app.product.scoring.manual_score_policy import (
    ManualScorePolicy,
    ManualScoreValidationError,
)


class FinalizationGateState(str, Enum):
    BLOCKED = "BLOCKED"
    READY = "READY"
    FINALIZED = "FINALIZED"


@dataclasses.dataclass(frozen=True)
class GateDecision:
    state: FinalizationGateState
    blockers: tuple[str, ...]
    answer_key: AnswerKey | None = dataclasses.field(default=None, repr=False)
    submissions: tuple[Submission, ...] = dataclasses.field(default=(), repr=False)
    draft_rows: tuple[dict[str, object], ...] = dataclasses.field(default=(), repr=False)


class FinalizationGate:
    def __init__(self, database: LocalDatabase) -> None:
        self.database = database
        self.storage = ProductRepository()

    def evaluate(self, session_id: str) -> GateDecision:
        blockers: list[str] = []
        with self.database.connection() as connection:
            session = self.storage.one(
                connection,
                "SELECT * FROM exam_sessions WHERE session_id = ?",
                (session_id,),
            )
            if session is None:
                return GateDecision(FinalizationGateState.BLOCKED, ("session_missing",))
            if session["state"] == "ARCHIVED":
                blockers.append("session_archived")
            if not session["teacher_confirmed"]:
                blockers.append("teacher_confirmation_missing")
            open_issues = self.storage.all(
                connection,
                """
                SELECT issue_type FROM review_issues
                WHERE session_id = ? AND state IN ('OPEN', 'IN_PROGRESS', 'BLOCKED')
                """,
                (session_id,),
            )
            blockers.extend(f"open_review:{row['issue_type']}" for row in open_issues)
            jobs = self.storage.all(
                connection,
                "SELECT * FROM capture_jobs WHERE session_id = ?",
                (session_id,),
            )
            if not jobs:
                blockers.append("capture_jobs_missing")
            for job in jobs:
                if job["state"] not in {"CONFIRMED", "EXCLUDED"}:
                    blockers.append(f"capture_not_confirmed:{job['id']}")
            draft_rows = self._draft_rows(connection, session_id)
            included_jobs = {job["id"] for job in jobs if job["state"] != "EXCLUDED"}
            draft_job_ids = {str(row["capture_job_id"]) for row in draft_rows}
            if included_jobs - draft_job_ids:
                blockers.append("recognition_draft_missing")
            identities = []
            submissions = []
            for row in draft_rows:
                if row["capture_job_id"] not in included_jobs:
                    continue
                provisional = row["provisional"]
                identity = provisional.get("identity") or {}
                student_id = str(identity.get("student_id") or "")
                if not student_id or not identity.get("confirmed"):
                    blockers.append(f"identity_unconfirmed:{row['capture_job_id']}")
                    continue
                if identity.get("temporary"):
                    blockers.append(f"temporary_student_unconfirmed:{student_id}")
                    continue
                identities.append(student_id)
                answers = {
                    int(number): normalize_answer(value)
                    for number, value in (provisional.get("answers") or {}).items()
                }
                raw_answers = {
                    int(number): str(value)
                    for number, value in (provisional.get("answers") or {}).items()
                }
                submissions.append(Submission(
                    student_id,
                    str(identity.get("name") or ""),
                    answers,
                    raw_answers,
                    (),
                    len(submissions) + 2,
                ))
            duplicates = [
                student_id
                for student_id, count in Counter(identities).items()
                if count > 1
            ]
            blockers.extend(f"duplicate_student:{item}" for item in duplicates)
            answer_key = self._answer_key(connection, session["answer_key_asset_id"])
            if answer_key is not None:
                blockers.extend(
                    self._manual_override_blockers(
                        connection,
                        session_id,
                        answer_key,
                    )
                )

        if answer_key is None:
            blockers.append("answer_key_missing")
        elif submissions:
            precheck = run_grading_precheck(
                answer_key=answer_key,
                submissions=submissions,
            )
            blockers.extend(f"precheck:{issue.code}" for issue in precheck.blocking)
        else:
            blockers.append("final_submissions_missing")

        confirmed = [
            TeacherConfirmedSubmission(
                job_id=str(row["capture_job_id"]),
                draft_snapshot={"blocking_errors": [], "review_items": []},
                confirmed_by="teacher",
                confirmed_at="confirmed",
                identity={"student_id": submission.student_id},
            )
            for row, submission in zip(
                [row for row in draft_rows if row["capture_job_id"] in included_jobs],
                submissions,
            )
        ]
        bridge = ExamOfficialReportGate().try_pass(confirmed, exam_id=session_id)
        if not bridge.ok:
            blockers.append(f"grading_bridge:{bridge.code.value}")
        unique_blockers = tuple(dict.fromkeys(blockers))
        return GateDecision(
            FinalizationGateState.BLOCKED if unique_blockers else FinalizationGateState.READY,
            unique_blockers,
            answer_key,
            tuple(submissions),
            tuple(draft_rows),
        )

    def _draft_rows(self, connection, session_id: str) -> list[dict[str, object]]:
        rows = self.storage.all(
            connection,
            "SELECT * FROM recognition_drafts WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        )
        return [
            {
                "id": row["id"],
                "capture_job_id": row["capture_job_id"],
                "provisional": json.loads(row["provisional_json"]),
            }
            for row in rows
        ]

    def _answer_key(self, connection, asset_id: str | None) -> AnswerKey | None:
        if not asset_id:
            return None
        row = self.storage.one(
            connection,
            "SELECT stored_path FROM exam_assets WHERE id = ? AND state = 'VALID'",
            (asset_id,),
        )
        return load_answer_key(Path(row["stored_path"])) if row else None

    def _manual_override_blockers(
        self,
        connection,
        session_id: str,
        answer_key: AnswerKey,
    ) -> list[str]:
        rows = self.storage.all(
            connection,
            """
            SELECT r.session_id AS resolution_session_id,
                   r.teacher_action, r.manual_score,
                   i.session_id AS issue_session_id,
                   i.capture_job_id, i.question_number,
                   j.session_id AS job_session_id
            FROM review_resolutions r
            JOIN review_issues i ON i.id = r.issue_id
            LEFT JOIN capture_jobs j ON j.id = i.capture_job_id
            WHERE i.session_id = ?
            """,
            (session_id,),
        )
        blockers = []
        for row in rows:
            job_id = row["capture_job_id"] or "missing"
            number = row["question_number"]
            suffix = f"{job_id}:{number if number is not None else 'missing'}"
            if row["resolution_session_id"] != session_id:
                blockers.append(f"manual_score_session_mismatch:{suffix}")
                continue
            if row["issue_session_id"] != session_id or row["job_session_id"] != session_id:
                blockers.append(f"manual_score_capture_mismatch:{suffix}")
                continue
            try:
                ManualScorePolicy.validate(
                    answer_key,
                    number,
                    row["teacher_action"],
                    row["manual_score"],
                )
            except ManualScoreValidationError as exc:
                blockers.append(f"{exc.code}:{suffix}")
        return blockers
