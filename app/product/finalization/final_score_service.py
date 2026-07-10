import dataclasses
import hashlib
import json
import shutil
import uuid
from pathlib import Path

from app.capture.capture_job import CaptureJobState
from app.domain.grading import grade_submission
from app.exam_session.session_model import ExamSessionState
from app.exam_session.session_repository import SessionRepository
from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now
from app.storage.repositories import ProductRepository
from app.storage.transaction import transaction

from .final_score_exporter import write_final_scores
from .finalization_audit import write_finalization_audit
from .finalization_gate import FinalizationGate, FinalizationGateState, GateDecision


@dataclasses.dataclass(frozen=True)
class FinalizationResult:
    session_id: str
    output_dir: Path
    generated_files: tuple[Path, ...]
    score_count: int


class FinalScoreService:
    def __init__(self, database: LocalDatabase, output_root: Path) -> None:
        self.database = database
        self.output_root = Path(output_root)
        self.storage = ProductRepository()
        self.sessions = SessionRepository()
        self.gate = FinalizationGate(database)
        initialize_database(database)

    def confirm_teacher(self, session_id: str, actor: str = "teacher") -> GateDecision:
        if not actor.strip():
            raise ValueError("confirmation actor is required")
        with transaction(self.database) as connection:
            session = self.sessions.get(connection, session_id)
            if session is None:
                raise ValueError("session does not exist")
            connection.execute(
                """
                UPDATE capture_jobs SET state = 'CONFIRMED', updated_at = ?
                WHERE session_id = ? AND state = 'PROVISIONAL_SCORED'
                """,
                (utc_now(), session_id),
            )
            self.sessions.update_state(
                connection,
                session_id,
                session.state,
                utc_now(),
                teacher_confirmed=True,
            )
        decision = self.gate.evaluate(session_id)
        target = (
            ExamSessionState.READY_TO_FINALIZE
            if decision.state is FinalizationGateState.READY
            else ExamSessionState.REVIEW_REQUIRED
        )
        with transaction(self.database) as connection:
            self.sessions.update_state(connection, session_id, target, utc_now())
        return self.gate.evaluate(session_id)

    def finalize(self, session_id: str, actor: str = "teacher") -> FinalizationResult:
        session = self._session(session_id)
        if session.state is not ExamSessionState.READY_TO_FINALIZE:
            raise ValueError("session must be READY_TO_FINALIZE")
        decision = self.gate.evaluate(session_id)
        if decision.state is not FinalizationGateState.READY:
            raise ValueError("finalization blocked: " + ", ".join(decision.blockers))
        rows, submission_payloads = self._build_scores(decision)
        output_dir = self.output_root / session_id
        stage = self.output_root / f".{session_id}_{uuid.uuid4().hex}.staging"
        stage.mkdir(parents=True, exist_ok=False)
        csv_path, json_path = write_final_scores(stage, rows)
        audit_path = write_finalization_audit(
            stage,
            {
                "session_id": session_id,
                "actor": actor,
                "finalized_at": utc_now(),
                "score_count": len(rows),
                "gate": "READY",
                "blockers": [],
            },
        )
        staged = (csv_path, json_path, audit_path)
        published: list[Path] = []
        try:
            with transaction(self.database) as connection:
                self._persist_final_records(
                    connection,
                    session,
                    rows,
                    submission_payloads,
                )
                output_dir.mkdir(parents=True, exist_ok=True)
                for path in staged:
                    target = output_dir / path.name
                    path.replace(target)
                    published.append(target)
                    self._record_artifact(connection, session, target)
                self.sessions.update_state(
                    connection,
                    session_id,
                    ExamSessionState.FINALIZED,
                    utc_now(),
                )
                self._audit(connection, session, actor, len(rows))
        except Exception:
            for path in published:
                path.unlink(missing_ok=True)
            raise
        finally:
            shutil.rmtree(stage, ignore_errors=True)
        return FinalizationResult(
            session_id,
            output_dir,
            tuple(published),
            len(rows),
        )

    def _build_scores(
        self,
        decision: GateDecision,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        rows = []
        submissions = []
        draft_by_student = {
            str(draft["provisional"]["identity"]["student_id"]): draft
            for draft in decision.draft_rows
            if (draft["provisional"].get("identity") or {}).get("student_id")
        }
        for submission in decision.submissions:
            result = grade_submission(decision.answer_key, submission)
            draft = draft_by_student[submission.student_id]
            overrides = self._manual_overrides(str(draft["capture_job_id"]))
            score = result.score
            for number, manual_score in overrides.items():
                detail = next(item for item in result.details if item.number == number)
                score += manual_score - detail.score
            score = round(score, 6)
            identity = draft["provisional"]["identity"]
            rows.append({
                "student_no": identity["student_no"],
                "student_name": identity["name"],
                "score": score,
                "max_score": result.max_score,
                "percent": round(score / result.max_score * 100, 2) if result.max_score else 0,
                "status": "FINAL",
                "unresolved_count": 0,
                "manual_review_count": len(overrides),
            })
            submissions.append({
                "student_id": submission.student_id,
                "answers": {
                    str(number): sorted(values)
                    for number, values in submission.answers.items()
                },
            })
        return rows, submissions

    def _manual_overrides(self, capture_job_id: str) -> dict[int, float]:
        with self.database.connection() as connection:
            rows = self.storage.all(
                connection,
                """
                SELECT i.question_number, r.teacher_action, r.manual_score
                FROM review_resolutions r
                JOIN review_issues i ON i.id = r.issue_id
                WHERE i.capture_job_id = ? AND i.question_number IS NOT NULL
                """,
                (capture_job_id,),
            )
        overrides = {}
        for row in rows:
            overrides[row["question_number"]] = (
                float(row["manual_score"])
                if row["teacher_action"] == "MANUAL_SCORE"
                else 0.0
            )
        return overrides

    def _persist_final_records(
        self,
        connection,
        session,
        rows: list[dict[str, object]],
        submissions: list[dict[str, object]],
    ) -> None:
        now = utc_now()
        for row, submission in zip(rows, submissions):
            self.storage.insert(connection, "final_submissions", {
                "id": uuid.uuid4().hex,
                "session_id": session.session_id,
                "class_id": session.class_id,
                "student_id": submission["student_id"],
                "answers_json": json.dumps(submission["answers"], ensure_ascii=False),
                "state": "FINAL",
                "created_at": now,
                "updated_at": now,
            })
            self.storage.insert(connection, "final_scores", {
                "id": uuid.uuid4().hex,
                "session_id": session.session_id,
                "class_id": session.class_id,
                "student_id": submission["student_id"],
                "student_no": row["student_no"],
                "student_name": row["student_name"],
                "score": row["score"],
                "max_score": row["max_score"],
                "percent": row["percent"],
                "unresolved_count": row["unresolved_count"],
                "manual_review_count": row["manual_review_count"],
                "state": "FINAL",
                "created_at": now,
                "updated_at": now,
            })

    def _record_artifact(self, connection, session, path: Path) -> None:
        now = utc_now()
        self.storage.insert(connection, "artifact_index", {
            "id": uuid.uuid4().hex,
            "session_id": session.session_id,
            "class_id": session.class_id,
            "artifact_type": path.name,
            "stored_path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "state": "PUBLISHED",
            "created_at": now,
            "updated_at": now,
        })

    def _audit(self, connection, session, actor: str, score_count: int) -> None:
        now = utc_now()
        self.storage.insert(connection, "audit_events", {
            "id": uuid.uuid4().hex,
            "session_id": session.session_id,
            "class_id": session.class_id,
            "entity_type": "exam_session",
            "entity_id": session.session_id,
            "action": "FINALIZE",
            "actor": actor,
            "payload_json": json.dumps({"score_count": score_count}),
            "state": "RECORDED",
            "created_at": now,
            "updated_at": now,
        })

    def _session(self, session_id: str):
        with self.database.connection() as connection:
            session = self.sessions.get(connection, session_id)
        if session is None:
            raise ValueError("session does not exist")
        return session
