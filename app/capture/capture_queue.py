import dataclasses
import hashlib
import os
import sqlite3
import uuid
from pathlib import Path

from app.exam_session.session_model import ExamSessionState
from app.exam_session.session_repository import SessionRepository
from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now
from app.storage.repositories import ProductRepository
from app.storage.transaction import transaction

from .capture_job import CaptureJob, CaptureJobState
from .capture_source import CaptureSourceType


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


@dataclasses.dataclass(frozen=True)
class CaptureRegistration:
    job: CaptureJob
    duplicate: bool = False
    warning: str = ""


class CaptureSessionNotFoundError(ValueError):
    pass


class CaptureSessionStateError(ValueError):
    pass


class CaptureClientConflictError(ValueError):
    pass


class CaptureQueue:
    def __init__(self, database: LocalDatabase, storage_root: Path) -> None:
        self.database = database
        self.storage_root = Path(storage_root)
        self.sessions = SessionRepository()
        self.storage = ProductRepository()
        initialize_database(database)

    def add_file(
        self,
        session_id: str,
        source: Path,
        source_type: CaptureSourceType,
    ) -> CaptureRegistration:
        source = Path(source)
        if source.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError("only JPG, JPEG and PNG images are supported")
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError("image file is missing or empty")
        return self.add_bytes(
            session_id,
            source.name,
            source.read_bytes(),
            source_type,
            source_path=str(source),
            source_mtime=source.stat().st_mtime,
        )

    def add_bytes(
        self,
        session_id: str,
        filename: str,
        content: bytes,
        source_type: CaptureSourceType,
        *,
        source_path: str = "",
        source_mtime: float = 0,
        client_capture_id: str = "",
        metadata_json: str = "{}",
    ) -> CaptureRegistration:
        suffix = Path(filename).suffix.lower()
        if suffix not in IMAGE_SUFFIXES:
            raise ValueError("only JPG, JPEG and PNG images are supported")
        if not content:
            raise ValueError("image payload is empty")
        digest = hashlib.sha256(content).hexdigest()
        target: Path | None = None
        temporary: Path | None = None
        try:
            with transaction(self.database) as connection:
                session = self.sessions.get(connection, session_id)
                if session is None:
                    raise CaptureSessionNotFoundError("session does not exist")
                if session.state not in {
                    ExamSessionState.CAPTURE_READY,
                    ExamSessionState.CAPTURING,
                    ExamSessionState.PROCESSING,
                    ExamSessionState.REVIEW_REQUIRED,
                }:
                    raise CaptureSessionStateError("session is not capture ready")
                if client_capture_id:
                    receipt = self._find_mobile_receipt(
                        connection,
                        session_id,
                        client_capture_id,
                    )
                    if receipt is not None:
                        receipt_job, receipt_digest = receipt
                        if receipt_digest != digest:
                            raise CaptureClientConflictError(
                                "client capture id is already bound to different content"
                            )
                        return CaptureRegistration(
                            receipt_job,
                            duplicate=True,
                            warning="该图片已进入队列。",
                        )
                duplicate = self._find_hash(connection, session_id, digest)
                if duplicate is not None:
                    if client_capture_id:
                        self._add_mobile_receipt(
                            connection,
                            session_id,
                            client_capture_id,
                            duplicate.capture_job_id,
                            digest,
                            metadata_json,
                        )
                    return CaptureRegistration(
                        duplicate,
                        duplicate=True,
                        warning="相同图片已在队列中，未重复创建任务。",
                    )
                job_id = uuid.uuid4().hex
                directory = self.storage_root / "uploads" / session_id
                directory.mkdir(parents=True, exist_ok=True)
                target = directory / f"{job_id}{suffix}"
                temporary = directory / f".{job_id}.part"
                temporary.write_bytes(content)
                os.replace(temporary, target)
                temporary = None
                now = utc_now()
                job = CaptureJob(
                    job_id,
                    session_id,
                    session.class_id,
                    source_type,
                    source_path,
                    str(target),
                    digest,
                    len(content),
                    source_mtime,
                    CaptureJobState.QUEUED,
                    now,
                    now,
                )
                self.storage.insert(
                    connection,
                    "capture_jobs",
                    self._values(job),
                )
                if client_capture_id:
                    self._add_mobile_receipt(
                        connection,
                        session_id,
                        client_capture_id,
                        job_id,
                        digest,
                        metadata_json,
                    )
                if session.state is ExamSessionState.CAPTURE_READY:
                    self.sessions.update_state(
                        connection,
                        session_id,
                        ExamSessionState.CAPTURING,
                        now,
                    )
        except Exception:
            for path in (temporary, target):
                if path is not None:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
            raise
        return CaptureRegistration(job)

    def list_jobs(self, session_id: str) -> list[CaptureJob]:
        with self.database.connection() as connection:
            rows = self.storage.all(
                connection,
                "SELECT * FROM capture_jobs WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            )
        return [self._map(row) for row in rows]

    def update_state(
        self,
        connection: sqlite3.Connection,
        job_id: str,
        state: CaptureJobState,
        error_code: str = "",
    ) -> None:
        connection.execute(
            """
            UPDATE capture_jobs
            SET state = ?, error_code = ?, updated_at = ?
            WHERE id = ?
            """,
            (state.value, error_code, utc_now(), job_id),
        )

    def mark_failed(self, job_id: str, error_code: str) -> None:
        with transaction(self.database) as connection:
            self.update_state(
                connection,
                job_id,
                CaptureJobState.FAILED,
                error_code,
            )

    def _find_hash(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        digest: str,
    ) -> CaptureJob | None:
        row = self.storage.one(
            connection,
            "SELECT * FROM capture_jobs WHERE session_id = ? AND sha256 = ?",
            (session_id, digest),
        )
        return self._map(row) if row else None

    def _find_mobile_receipt(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        client_capture_id: str,
    ) -> tuple[CaptureJob, str] | None:
        row = self.storage.one(
            connection,
            """
            SELECT capture_jobs.*, mobile_capture_receipts.sha256 AS receipt_sha256
            FROM mobile_capture_receipts
            JOIN capture_jobs
              ON capture_jobs.id = mobile_capture_receipts.capture_job_id
            WHERE mobile_capture_receipts.session_id = ?
              AND mobile_capture_receipts.client_capture_id = ?
            """,
            (session_id, client_capture_id),
        )
        if row is None:
            return None
        return self._map(row), row["receipt_sha256"]

    def _add_mobile_receipt(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        client_capture_id: str,
        capture_job_id: str,
        digest: str,
        metadata_json: str,
    ) -> None:
        now = utc_now()
        connection.execute(
            """
            INSERT INTO mobile_capture_receipts (
                id, session_id, client_capture_id, capture_job_id, sha256,
                metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                session_id,
                client_capture_id,
                capture_job_id,
                digest,
                metadata_json,
                now,
                now,
            ),
        )

    @staticmethod
    def _values(job: CaptureJob) -> dict[str, object]:
        return {
            "id": job.capture_job_id,
            "session_id": job.session_id,
            "class_id": job.class_id,
            "source_type": job.source_type.value,
            "source_path": job.source_path,
            "stored_image_path": job.stored_image_path,
            "sha256": job.sha256,
            "source_size": job.source_size,
            "source_mtime": job.source_mtime,
            "state": job.state.value,
            "error_code": job.error_code,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }

    @staticmethod
    def _map(row: sqlite3.Row) -> CaptureJob:
        return CaptureJob(
            row["id"],
            row["session_id"],
            row["class_id"],
            CaptureSourceType(row["source_type"]),
            row["source_path"],
            row["stored_image_path"],
            row["sha256"],
            row["source_size"],
            row["source_mtime"],
            CaptureJobState(row["state"]),
            row["created_at"],
            row["updated_at"],
            row["error_code"],
        )
