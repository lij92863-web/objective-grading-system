import json
import sqlite3

from app.storage.repositories import ProductRepository

from .roster_validator import Student


class RosterRepository:
    def __init__(self) -> None:
        self.storage = ProductRepository()

    def add_many(
        self,
        connection: sqlite3.Connection,
        students: list[Student],
    ) -> None:
        for student in students:
            self.storage.insert(
                connection,
                "students",
                {
                    "id": student.student_id,
                    "class_id": student.class_id,
                    "student_no": student.student_no,
                    "name": student.name,
                    "aliases": json.dumps(student.aliases, ensure_ascii=False),
                    "state": student.status,
                    "created_at": student.created_at,
                    "updated_at": student.updated_at,
                },
            )

    def list_for_class(
        self,
        connection: sqlite3.Connection,
        class_id: str,
    ) -> list[Student]:
        rows = self.storage.all(
            connection,
            "SELECT * FROM students WHERE class_id = ? ORDER BY student_no",
            (class_id,),
        )
        return [
            Student(
                student_id=row["id"],
                class_id=row["class_id"],
                student_no=row["student_no"],
                name=row["name"],
                aliases=tuple(json.loads(row["aliases"])),
                status=row["state"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
