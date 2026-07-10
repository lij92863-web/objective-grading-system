import uuid

from app.classes.class_repository import ClassRepository
from app.storage.local_db import LocalDatabase
from app.storage.migrations import initialize_database, utc_now
from app.storage.transaction import transaction

from .session_model import ExamSession, ExamSessionState
from .session_repository import SessionRepository


class SessionService:
    def __init__(self, database: LocalDatabase) -> None:
        self.database = database
        self.sessions = SessionRepository()
        self.classes = ClassRepository()
        initialize_database(database)

    def create_session(self, exam_name: str, class_id: str) -> ExamSession:
        name = exam_name.strip()
        if not name:
            raise ValueError("exam name is required")
        now = utc_now()
        session = ExamSession(
            uuid.uuid4().hex,
            name,
            class_id,
            None,
            None,
            None,
            False,
            ExamSessionState.CLASS_SELECTED,
            now,
            now,
        )
        with transaction(self.database) as connection:
            if self.classes.get(connection, class_id) is None:
                raise ValueError("class does not exist")
            self.sessions.add(connection, session)
        return session

    def get_session(self, session_id: str) -> ExamSession | None:
        with self.database.connection() as connection:
            return self.sessions.get(connection, session_id)

    def list_sessions(self) -> list[ExamSession]:
        with self.database.connection() as connection:
            return self.sessions.list(connection)

    def start_capture(self, session_id: str) -> ExamSession:
        with transaction(self.database) as connection:
            session = self.sessions.get(connection, session_id)
            if session is None:
                raise ValueError("session does not exist")
            if session.state is not ExamSessionState.CAPTURE_READY:
                raise ValueError("session is not capture ready")
            self.sessions.update_state(
                connection,
                session_id,
                ExamSessionState.CAPTURING,
                utc_now(),
            )
        return self.get_session(session_id)
