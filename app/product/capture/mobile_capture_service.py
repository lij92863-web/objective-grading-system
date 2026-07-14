import dataclasses

from app.capture import CaptureJobState, CaptureQueue, CaptureSourceType
from app.capture.mobile_web_camera_source import MobileWebCameraSource
from app.classes.class_repository import ClassRepository
from app.exam_session.session_model import ExamSessionState
from app.exam_session.session_repository import SessionRepository
from app.product.pipeline import MockRecognitionInput, ProductPipeline
from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now


CAPTURE_ALLOWED_STATES = {
    ExamSessionState.CAPTURE_READY,
    ExamSessionState.CAPTURING,
    ExamSessionState.PROCESSING,
    ExamSessionState.REVIEW_REQUIRED,
}
RECENT_CAPTURE_LIMIT = 20


class MobileCaptureServiceError(ValueError):
    def __init__(self, message: str, status: int, code: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


@dataclasses.dataclass(frozen=True)
class MobileCaptureOutcome:
    capture_job_id: str
    duplicate: bool
    state: str
    warning: str
    server_received_at: str


@dataclasses.dataclass(frozen=True)
class MobileSessionSummary:
    session_id: str
    exam_name: str
    class_name: str
    state: str
    captured_count: int


class MobileCaptureService:
    def __init__(
        self,
        database: LocalDatabase,
        queue: CaptureQueue,
        pipeline: ProductPipeline,
    ) -> None:
        self.database = database
        self.queue = queue
        self.pipeline = pipeline
        self.source = MobileWebCameraSource(queue)
        self.sessions = SessionRepository()
        self.classes = ClassRepository()
        initialize_database(database)

    def ingest(
        self,
        session_id: str,
        filename: str,
        content: bytes,
        file_mime_type: str,
        fields: dict[str, str],
    ) -> MobileCaptureOutcome:
        registration = self.source.upload_blob(
            session_id,
            filename,
            content,
            file_mime_type,
            fields,
        )
        warning = registration.warning
        if not registration.duplicate or registration.job.state is CaptureJobState.QUEUED:
            try:
                self.pipeline.process_mock(
                    registration.job.capture_job_id,
                    MockRecognitionInput(
                        evidence_path=registration.job.stored_image_path,
                    ),
                )
            except Exception:
                self.queue.mark_failed(
                    registration.job.capture_job_id,
                    "CONSERVATIVE_PIPELINE_FAILED",
                )
                warning = "图片已可靠入队，但保守处理失败，请在电脑端检查。"
        return MobileCaptureOutcome(
            capture_job_id=registration.job.capture_job_id,
            duplicate=registration.duplicate,
            state=registration.job.state.value,
            warning=warning,
            server_received_at=utc_now(),
        )

    def available_sessions(self) -> list[MobileSessionSummary]:
        summaries: list[MobileSessionSummary] = []
        with self.database.connection() as connection:
            for session in self.sessions.list(connection):
                if session.state not in CAPTURE_ALLOWED_STATES:
                    continue
                classroom = self.classes.get(connection, session.class_id)
                if classroom is None:
                    continue
                count = connection.execute(
                    "SELECT COUNT(*) FROM capture_jobs WHERE session_id = ?",
                    (session.session_id,),
                ).fetchone()[0]
                summaries.append(MobileSessionSummary(
                    session.session_id,
                    session.exam_name,
                    classroom.class_name,
                    session.state.value,
                    int(count),
                ))
        return summaries

    def session_summary(self, session_id: str) -> MobileSessionSummary:
        with self.database.connection() as connection:
            session = self.sessions.get(connection, session_id)
            if session is None:
                raise MobileCaptureServiceError(
                    "考试会话不存在。",
                    404,
                    "SESSION_NOT_FOUND",
                )
            if session.state not in CAPTURE_ALLOWED_STATES:
                raise MobileCaptureServiceError(
                    "当前考试状态不允许采集。",
                    409,
                    "SESSION_NOT_CAPTURE_READY",
                )
            classroom = self.classes.get(connection, session.class_id)
            if classroom is None:
                raise MobileCaptureServiceError(
                    "考试班级不存在。",
                    409,
                    "SESSION_CLASS_MISSING",
                )
            count = connection.execute(
                "SELECT COUNT(*) FROM capture_jobs WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
        return MobileSessionSummary(
            session.session_id,
            session.exam_name,
            classroom.class_name,
            session.state.value,
            int(count),
        )

    def status(self, session_id: str) -> dict[str, object]:
        with self.database.connection() as connection:
            session = self.sessions.get(connection, session_id)
            if session is None:
                raise MobileCaptureServiceError(
                    "考试会话不存在。",
                    404,
                    "SESSION_NOT_FOUND",
                )
            rows = connection.execute(
                """
                SELECT id, state, source_type, created_at, error_code
                FROM capture_jobs
                WHERE session_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (session_id,),
            ).fetchall()
        counts = {
            "total": len(rows),
            "queued": 0,
            "processing": 0,
            "review_required": 0,
            "confirmed": 0,
            "excluded": 0,
            "failed": 0,
            "mobile_total": 0,
        }
        queued = {"CREATED", "QUEUED", "IMAGE_READY"}
        processing = {"RECOGNIZED", "PROVISIONAL_SCORED"}
        failed = {"QUALITY_FAILED", "PAGE_FAILED", "FAILED"}
        for row in rows:
            state = row["state"]
            if state in queued:
                counts["queued"] += 1
            elif state in processing:
                counts["processing"] += 1
            elif state == "REVIEW_REQUIRED":
                counts["review_required"] += 1
            elif state == "CONFIRMED":
                counts["confirmed"] += 1
            elif state == "EXCLUDED":
                counts["excluded"] += 1
            elif state in failed:
                counts["failed"] += 1
            if row["source_type"] == CaptureSourceType.MOBILE_WEB_USB_CAMERA.value:
                counts["mobile_total"] += 1
        recent = [
            {
                "capture_job_id": row["id"],
                "state": row["state"],
                "source_type": row["source_type"],
                "created_at": row["created_at"],
                "error_code": row["error_code"],
            }
            for row in rows[:RECENT_CAPTURE_LIMIT]
        ]
        return {
            "ok": True,
            "session_id": session_id,
            "session_state": session.state.value,
            "counts": counts,
            "recent": recent,
        }
