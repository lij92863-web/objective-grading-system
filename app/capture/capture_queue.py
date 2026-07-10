import dataclasses
import hashlib
import shutil
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
    ) -> CaptureRegistration:
        suffix = Path(filename).suffix.lower()
        if suffix not in IMAGE_SUFFIXES:
            raise ValueError("only JPG, JPEG and PNG images are supported")
        if not content:
            raise ValueError("image payload is empty")
        digest = hashlib.sha256(content).hexdigest()
        with transaction(self.database) as connection:
            session = self.sessions.get(connection, session_id)
            if session is None:
                raise ValueError("session does not exist")
            if session.state not in {
                ExamSessionState.CAPTURE_READY,
                ExamSessionState.CAPTURING,
            }:
                raise ValueError("session is not capture ready")
            duplicate = self._find_hash(connection, session_id, digest)
            if duplicate is not None:
                return CaptureRegistration(
                    duplicate,
                    duplicate=True,
                    warning="相同图片已在队列中，未重复创建任务。",
                )
            job_id = uuid.uuid4().hex
            directory = self.storage_root / "uploads" / session_id
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / f"{job_id}{suffix}"
            target.write_bytes(content)
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
            if session.state is ExamSessionState.CAPTURE_READY:
                self.sessions.update_state(
                    connection,
                    session_id,
                    ExamSessionState.CAPTURING,
                    now,
                )
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
