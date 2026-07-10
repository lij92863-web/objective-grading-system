import hashlib
import shutil
import uuid
from pathlib import Path

from app.domain.grading import AnswerKey
from app.infrastructure.loaders.csv_loaders import load_answer_key
from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now
from app.storage.transaction import transaction

from .asset_model import AssetRegistration, AssetType, ExamAsset
from .asset_repository import AssetRepository
from .session_model import ExamSessionState
from .session_repository import SessionRepository


class AssetService:
    def __init__(self, database: LocalDatabase, storage_root: Path) -> None:
        self.database = database
        self.storage_root = Path(storage_root)
        self.assets = AssetRepository()
        self.sessions = SessionRepository()
        initialize_database(database)

    def register(
        self,
        session_id: str,
        source: Path,
        asset_type: AssetType,
    ) -> AssetRegistration:
        source = Path(source)
        if not source.is_file():
            raise ValueError("asset file does not exist")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        with transaction(self.database) as connection:
            session = self.sessions.get(connection, session_id)
            if session is None:
                raise ValueError("session does not exist")
            if session.state in {
                ExamSessionState.FINALIZED,
                ExamSessionState.ARCHIVED,
            }:
                raise ValueError("finalized or archived session is read-only")
            duplicate = self.assets.find_hash(connection, session_id, digest)
            if duplicate is not None:
                return AssetRegistration(
                    duplicate,
                    duplicate=True,
                    warning="相同材料已存在，未重复保存。",
                )
            status = self._validate(source, asset_type)
            asset_id = uuid.uuid4().hex
            directory = self.storage_root / "assets" / session_id
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / f"{asset_id}_{source.name}"
            shutil.copy2(source, target)
            now = utc_now()
            asset = ExamAsset(
                asset_id,
                session_id,
                session.class_id,
                asset_type,
                source.name,
                str(target),
                digest,
                status,
                now,
                now,
            )
            self.assets.add(connection, asset)
            answer_id = session.answer_key_asset_id
            paper_id = session.paper_asset_id
            template_id = session.template_id
            if status == "VALID":
                if asset_type is AssetType.ANSWER_KEY:
                    answer_id = asset_id
                elif asset_type is AssetType.PAPER:
                    paper_id = asset_id
                elif asset_type is AssetType.TEMPLATE:
                    template_id = asset_id
            state = self._readiness(answer_id, template_id)
            self.sessions.update_assets_and_state(
                connection,
                session_id,
                answer_key_asset_id=answer_id,
                paper_asset_id=paper_id,
                template_id=template_id,
                state=state,
                updated_at=now,
            )
        return AssetRegistration(asset)

    def list_assets(self, session_id: str) -> list[ExamAsset]:
        with self.database.connection() as connection:
            return self.assets.list_for_session(connection, session_id)

    @staticmethod
    def _validate(source: Path, asset_type: AssetType) -> str:
        if asset_type is AssetType.ANSWER_KEY:
            try:
                answer_key = load_answer_key(source)
            except Exception:
                return "ASSET_INVALID"
            if not isinstance(answer_key, AnswerKey):
                return "ASSET_INVALID"
        return "VALID"

    @staticmethod
    def _readiness(
        answer_key_asset_id: str | None,
        template_id: str | None,
    ) -> ExamSessionState:
        if answer_key_asset_id and template_id:
            return ExamSessionState.CAPTURE_READY
        if answer_key_asset_id:
            return ExamSessionState.ASSET_READY
        return ExamSessionState.CLASS_SELECTED
