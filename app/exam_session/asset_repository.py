import sqlite3

from app.storage.repositories import ProductRepository

from .asset_model import AssetType, ExamAsset


class AssetRepository:
    def __init__(self) -> None:
        self.storage = ProductRepository()

    def add(self, connection: sqlite3.Connection, asset: ExamAsset) -> None:
        self.storage.insert(
            connection,
            "exam_assets",
            {
                "id": asset.asset_id,
                "session_id": asset.session_id,
                "class_id": asset.class_id,
                "asset_type": asset.asset_type.value,
                "original_filename": asset.original_filename,
                "stored_path": asset.stored_path,
                "sha256": asset.sha256,
                "state": asset.status,
                "created_at": asset.created_at,
                "updated_at": asset.updated_at,
            },
        )

    def find_hash(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        sha256: str,
    ) -> ExamAsset | None:
        row = self.storage.one(
            connection,
            "SELECT * FROM exam_assets WHERE session_id = ? AND sha256 = ?",
            (session_id, sha256),
        )
        return self._map(row) if row else None

    def list_for_session(
        self,
        connection: sqlite3.Connection,
        session_id: str,
    ) -> list[ExamAsset]:
        rows = self.storage.all(
            connection,
            "SELECT * FROM exam_assets WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        )
        return [self._map(row) for row in rows]

    @staticmethod
    def _map(row: sqlite3.Row) -> ExamAsset:
        return ExamAsset(
            asset_id=row["id"],
            session_id=row["session_id"],
            class_id=row["class_id"],
            asset_type=AssetType(row["asset_type"]),
            original_filename=row["original_filename"],
            stored_path=row["stored_path"],
            sha256=row["sha256"],
            status=row["state"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
