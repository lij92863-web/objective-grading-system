import sqlite3

from app.storage.repositories import ProductRepository

from .class_model import ClassRoom, ClassState


class ClassRepository:
    def __init__(self) -> None:
        self.storage = ProductRepository()

    def add(self, connection: sqlite3.Connection, classroom: ClassRoom) -> None:
        self.storage.insert(
            connection,
            "classes",
            {
                "id": classroom.class_id,
                "class_name": classroom.class_name,
                "grade_name": classroom.grade_name,
                "school_year": classroom.school_year,
                "state": classroom.status.value,
                "created_at": classroom.created_at,
                "updated_at": classroom.updated_at,
            },
        )

    def get(
        self,
        connection: sqlite3.Connection,
        class_id: str,
    ) -> ClassRoom | None:
        row = self.storage.one(
            connection,
            "SELECT * FROM classes WHERE id = ?",
            (class_id,),
        )
        return self._map(row) if row else None

    def list(self, connection: sqlite3.Connection) -> list[ClassRoom]:
        rows = self.storage.all(
            connection,
            "SELECT * FROM classes ORDER BY created_at, class_name",
        )
        return [self._map(row) for row in rows]

    @staticmethod
    def _map(row: sqlite3.Row) -> ClassRoom:
        return ClassRoom(
            class_id=row["id"],
            class_name=row["class_name"],
            grade_name=row["grade_name"],
            school_year=row["school_year"],
            status=ClassState(row["state"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
