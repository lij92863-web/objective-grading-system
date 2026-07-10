import uuid

from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now
from app.storage.transaction import transaction

from .class_model import ClassRoom, ClassState
from .class_repository import ClassRepository


class ClassService:
    def __init__(self, database: LocalDatabase) -> None:
        self.database = database
        self.repository = ClassRepository()
        initialize_database(database)

    def create_class(
        self,
        class_name: str,
        grade_name: str = "",
        school_year: str = "",
    ) -> ClassRoom:
        name = class_name.strip()
        if not name:
            raise ValueError("class name is required")
        now = utc_now()
        classroom = ClassRoom(
            class_id=uuid.uuid4().hex,
            class_name=name,
            grade_name=grade_name.strip(),
            school_year=school_year.strip(),
            status=ClassState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        with transaction(self.database) as connection:
            self.repository.add(connection, classroom)
        return classroom

    def get_class(self, class_id: str) -> ClassRoom | None:
        with self.database.connection() as connection:
            return self.repository.get(connection, class_id)

    def list_classes(self) -> list[ClassRoom]:
        with self.database.connection() as connection:
            return self.repository.list(connection)
