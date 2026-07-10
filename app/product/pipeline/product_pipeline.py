import dataclasses
import json
from pathlib import Path
from typing import Mapping

from app.capture.capture_job import CaptureJobState
from app.capture.capture_queue import CaptureQueue
from app.exam_session.session_model import ExamSessionState
from app.exam_session.session_repository import SessionRepository
from app.infrastructure.loaders.csv_loaders import load_answer_key
from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now
from app.storage.repositories import ProductRepository
from app.storage.transaction import transaction

from app.product.review.review_issue_classifier import ReviewIssueType

from .pipeline_repository import PipelineRepository
from .provisional_scoring import build_provisional_score


@dataclasses.dataclass(frozen=True)
class MockRecognitionInput:
    student_no: str = ""
    name: str = ""
    answer_candidates: Mapping[int, str | None] = dataclasses.field(default_factory=dict)
    quality_ok: bool = True
    page_ok: bool = True
    evidence_path: str = ""


@dataclasses.dataclass(frozen=True)
class ProductPipelineResult:
    capture_job_id: str
    draft_id: str
    provisional_score: float | None
    issue_ids: tuple[str, ...]
    state: CaptureJobState


class ProductPipeline:
    def __init__(self, database: LocalDatabase, storage_root: Path) -> None:
        self.database = database
        self.storage_root = Path(storage_root)
        self.repository = PipelineRepository()
        self.storage = ProductRepository()
        self.sessions = SessionRepository()
        self.capture = CaptureQueue(database, storage_root)
        initialize_database(database)

    def process_mock(
        self,
        capture_job_id: str,
        recognition: MockRecognitionInput,
    ) -> ProductPipelineResult:
        with transaction(self.database) as connection:
            job = self.repository.get_job(connection, capture_job_id)
            if job is None:
                raise ValueError("capture job does not exist")
            session = self.sessions.get(connection, job["session_id"])
            if session is None:
                raise ValueError("session does not exist")
            answer_path = self._answer_key_path(connection, session.answer_key_asset_id)
            answer_key = load_answer_key(answer_path)
            evidence = {
                "student_no": recognition.student_no,
                "name": recognition.name,
                "answer_candidates": dict(recognition.answer_candidates),
                "quality_ok": recognition.quality_ok,
                "page_ok": recognition.page_ok,
                "evidence_path": recognition.evidence_path,
            }
            issue_specs: list[tuple[ReviewIssueType, int | None, dict[str, object]]] = []
            provisional_payload: dict[str, object] = {
                "identity": {},
                "answers": {},
                "question_scores": {},
                "score": None,
                "max_score": answer_key.total_points,
                "official": False,
            }
            if not recognition.quality_ok:
                issue_specs.append((ReviewIssueType.PAGE_QUALITY_FAILED, None, {}))
            elif not recognition.page_ok:
                issue_specs.append((ReviewIssueType.PAGE_LOCATION_FAILED, None, {}))
            else:
                student, exact_number = self.repository.find_student(
                    connection,
                    session.class_id,
                    recognition.student_no.strip(),
                    recognition.name.strip(),
                )
                duplicate_identity = bool(
                    student is not None
                    and exact_number
                    and self.repository.identity_already_used(
                        connection,
                        session.session_id,
                        student["id"],
                    )
                )
                if student is None:
                    issue_specs.append((ReviewIssueType.IDENTITY_MISSING, None, {}))
                elif duplicate_identity:
                    issue_specs.append((ReviewIssueType.IDENTITY_DUPLICATE, None, {}))
                elif not exact_number:
                    issue_specs.append((ReviewIssueType.IDENTITY_MISSING, None, {}))
                if student is not None:
                    provisional_payload["identity"] = {
                        "student_id": student["id"],
                        "student_no": student["student_no"],
                        "name": student["name"],
                        "confirmed": exact_number and not duplicate_identity,
                    }
                provisional = build_provisional_score(
                    answer_key,
                    recognition.answer_candidates,
                )
                provisional_payload.update({
                    "answers": dict(provisional.readable_answers),
                    "question_scores": dict(provisional.question_scores),
                    "score": provisional.score,
                    "max_score": provisional.max_score,
                })
                for number in provisional.unreadable_questions:
                    issue_specs.append((
                        ReviewIssueType.ANSWER_UNREADABLE,
                        number,
                        {"question_number": number},
                    ))
            state = (
                CaptureJobState.REVIEW_REQUIRED
                if issue_specs
                else CaptureJobState.PROVISIONAL_SCORED
            )
            draft_id = self.repository.add_draft(
                connection,
                session_id=session.session_id,
                class_id=session.class_id,
                job_id=capture_job_id,
                evidence=evidence,
                provisional=provisional_payload,
                state="PROVISIONAL",
            )
            issue_ids = tuple(
                self.repository.add_issue(
                    connection,
                    session_id=session.session_id,
                    class_id=session.class_id,
                    job_id=capture_job_id,
                    issue_type=issue_type,
                    question_number=question_number,
                    evidence_path=recognition.evidence_path,
                    payload=payload,
                )
                for issue_type, question_number, payload in issue_specs
            )
            self.capture.update_state(connection, capture_job_id, state)
            session_state = (
                ExamSessionState.REVIEW_REQUIRED
                if issue_specs
                else ExamSessionState.PROCESSING
            )
            self.sessions.update_state(
                connection,
                session.session_id,
                session_state,
                utc_now(),
            )
        return ProductPipelineResult(
            capture_job_id,
            draft_id,
            provisional_payload["score"],
            issue_ids,
            state,
        )

    def _answer_key_path(
        self,
        connection,
        answer_key_asset_id: str | None,
    ) -> Path:
        if not answer_key_asset_id:
            raise ValueError("session has no valid answer key")
        row = self.storage.one(
            connection,
            "SELECT stored_path FROM exam_assets WHERE id = ? AND state = 'VALID'",
            (answer_key_asset_id,),
        )
        if row is None:
            raise ValueError("valid answer key asset is unavailable")
        return Path(row["stored_path"])
