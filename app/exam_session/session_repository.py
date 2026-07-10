import sqlite3

from app.storage.repositories import ProductRepository

from .session_model import ExamSession, ExamSessionState


class SessionRepository:
    def __init__(self) -> None:
        self.storage = ProductRepository()

    def add(self, connection: sqlite3.Connection, session: ExamSession) -> None:
        self.storage.insert(
            connection,
            "exam_sessions",
            {
                "id": session.session_id,
                "session_id": session.session_id,
                "class_id": session.class_id,
                "exam_name": session.exam_name,
                "answer_key_asset_id": session.answer_key_asset_id,
                "paper_asset_id": session.paper_asset_id,
                "template_id": session.template_id,
                "teacher_confirmed": int(session.teacher_confirmed),
                "state": session.state.value,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            },
        )

    def get(
        self,
        connection: sqlite3.Connection,
        session_id: str,
    ) -> ExamSession | None:
        row = self.storage.one(
            connection,
            "SELECT * FROM exam_sessions WHERE session_id = ?",
            (session_id,),
        )
        return self._map(row) if row else None

    def list(self, connection: sqlite3.Connection) -> list[ExamSession]:
        return [
            self._map(row)
            for row in self.storage.all(
                connection,
                "SELECT * FROM exam_sessions ORDER BY created_at DESC",
            )
        ]

    def update_assets_and_state(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        *,
        answer_key_asset_id: str | None,
        paper_asset_id: str | None,
        template_id: str | None,
        state: ExamSessionState,
        updated_at: str,
    ) -> None:
        connection.execute(
            """
            UPDATE exam_sessions
            SET answer_key_asset_id = ?, paper_asset_id = ?, template_id = ?,
                state = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (
                answer_key_asset_id,
                paper_asset_id,
                template_id,
                state.value,
                updated_at,
                session_id,
            ),
        )

    def update_state(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        state: ExamSessionState,
        updated_at: str,
        teacher_confirmed: bool | None = None,
    ) -> None:
        if teacher_confirmed is None:
            connection.execute(
                "UPDATE exam_sessions SET state = ?, updated_at = ? WHERE session_id = ?",
                (state.value, updated_at, session_id),
            )
        else:
            connection.execute(
                """
                UPDATE exam_sessions
                SET state = ?, teacher_confirmed = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (state.value, int(teacher_confirmed), updated_at, session_id),
            )

    @staticmethod
    def _map(row: sqlite3.Row) -> ExamSession:
        return ExamSession(
            session_id=row["session_id"],
            exam_name=row["exam_name"],
            class_id=row["class_id"],
            answer_key_asset_id=row["answer_key_asset_id"],
            paper_asset_id=row["paper_asset_id"],
            template_id=row["template_id"],
            teacher_confirmed=bool(row["teacher_confirmed"]),
            state=ExamSessionState(row["state"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
