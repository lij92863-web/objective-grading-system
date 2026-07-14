import dataclasses
import uuid
from pathlib import Path

from app.capture import CaptureQueue
from app.capture.browser_camera_source import BrowserCameraSource
from app.capture.upload_source import ManualUploadSource
from app.capture.watched_folder_source import WatchedFolderSource
from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.product.capture import MobileCaptureService
from app.product.finalization import FinalScoreService
from app.product.pipeline import MockRecognitionInput, ProductPipeline
from app.product.review.manual_resolution import TeacherAction
from app.product.review.review_workflow import ReviewWorkflow
from app.roster.roster_importer import RosterImporter
from app.roster.roster_mapping import RosterColumnMapping
from app.storage import LocalDatabase


@dataclasses.dataclass(frozen=True)
class ProductPaths:
    root: Path
    database: Path
    incoming: Path
    exports: Path


class ProductFacade:
    def __init__(self, paths: ProductPaths) -> None:
        self.paths = paths
        self.database = LocalDatabase(paths.database)
        self.classes = ClassService(self.database)
        self.rosters = RosterImporter(self.database)
        self.sessions = SessionService(self.database)
        self.assets = AssetService(self.database, paths.root)
        self.queue = CaptureQueue(self.database, paths.root)
        self.pipeline = ProductPipeline(self.database, paths.root)
        self.mobile_capture = MobileCaptureService(
            self.database,
            self.queue,
            self.pipeline,
        )
        self.review = ReviewWorkflow(self.database)
        self.final_scores = FinalScoreService(self.database, paths.exports)

    def create_class(self, name: str, grade: str = "", year: str = ""):
        return self.classes.create_class(name, grade, year)

    def import_roster(
        self,
        class_id: str,
        filename: str,
        content: bytes,
        student_no_column: str = "",
        name_column: str = "",
        class_column: str = "",
    ):
        path = self._save_incoming(filename, content)
        mapping = None
        if student_no_column and name_column:
            mapping = RosterColumnMapping(
                student_no_column,
                name_column,
                class_column,
            )
        return self.rosters.import_file(class_id, path, mapping)

    def create_session(self, exam_name: str, class_id: str):
        return self.sessions.create_session(exam_name, class_id)

    def add_asset(
        self,
        session_id: str,
        asset_type: str,
        filename: str,
        content: bytes,
    ):
        path = self._save_incoming(filename, content)
        return self.assets.register(session_id, path, AssetType(asset_type))

    def capture_upload(
        self,
        session_id: str,
        filename: str,
        content: bytes,
        browser_camera: bool = False,
    ):
        if browser_camera:
            result = BrowserCameraSource(self.queue).upload_blob(
                session_id,
                filename,
                content,
            )
        else:
            path = self._save_incoming(filename, content)
            result = ManualUploadSource(self.queue).upload(session_id, path)
        if not result.duplicate:
            self._conservative_process(result.job)
        return result

    def scan_folder(self, session_id: str, folder: str):
        result = WatchedFolderSource(self.queue).scan(session_id, Path(folder))
        for registration in result.created:
            self._conservative_process(registration.job)
        return result

    def capture_mobile_web(
        self,
        session_id: str,
        filename: str,
        content: bytes,
        content_type: str,
        fields: dict[str, str],
    ):
        return self.mobile_capture.ingest(
            session_id,
            filename,
            content,
            content_type,
            fields,
        )

    def mobile_capture_status(self, session_id: str) -> dict[str, object]:
        return self.mobile_capture.status(session_id)

    def mobile_capture_sessions(self):
        return self.mobile_capture.available_sessions()

    def mobile_capture_session(self, session_id: str):
        return self.mobile_capture.session_summary(session_id)

    def resolve_issue(self, issue_id: str, values: dict[str, str]) -> None:
        issue_type = values.get("issue_type", "")
        if issue_type.startswith("IDENTITY_"):
            if values.get("exclude_capture") == "yes":
                self.review.exclude_capture_from_identity_issue(
                    issue_id,
                    reason=values.get("reason", ""),
                )
                return
            self.review.resolve_identity(
                issue_id,
                student_no=values.get("student_no", ""),
                name=values.get("name", ""),
                confirm_name=values.get("confirm_name") == "yes",
                temporary_reason=values.get("reason", ""),
            )
            return
        action = TeacherAction(values.get("action", "MARK_WRONG"))
        manual = values.get("manual_score", "").strip()
        self.review.resolve_answer(
            issue_id,
            action,
            manual_score=manual if manual else None,
            reason=values.get("reason", ""),
        )

    def finalize(self, session_id: str):
        decision = self.final_scores.confirm_teacher(session_id)
        if decision.blockers:
            return decision, None
        return decision, self.final_scores.finalize(session_id)

    def _conservative_process(self, job) -> None:
        self.pipeline.process_mock(
            job.capture_job_id,
            MockRecognitionInput(evidence_path=job.stored_image_path),
        )

    def _save_incoming(self, filename: str, content: bytes) -> Path:
        safe_name = Path(filename).name
        if not safe_name:
            raise ValueError("uploaded file needs a filename")
        self.paths.incoming.mkdir(parents=True, exist_ok=True)
        path = self.paths.incoming / f"{uuid.uuid4().hex}_{safe_name}"
        path.write_bytes(content)
        return path
