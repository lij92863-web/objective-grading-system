from pathlib import Path

from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.exam_session.session_model import ExamSessionState
from app.exam_session.session_repository import SessionRepository
from app.storage import LocalDatabase
from app.storage.migrations import utc_now
from app.storage.transaction import transaction
from app.web_product import ProductWebController, UploadedFile


JPEG = b"\xff\xd8\xff\xe0synthetic-mobile-jpeg"
PNG = b"\x89PNG\r\n\x1a\nsynthetic-mobile-png"


def mobile_fields(client_capture_id: str = "capture-test-001") -> dict[str, str]:
    return {
        "client_capture_id": client_capture_id,
        "captured_at": "2026-07-14T08:00:00.000Z",
        "capture_method": "IMAGE_CAPTURE",
        "device_label": "Synthetic rear camera",
        "device_id": "0123456789abcdef",
        "facing_mode": "environment",
        "width": "3840",
        "height": "2160",
        "mime_type": "image/jpeg",
    }


def prepare_session(root: Path):
    database = LocalDatabase(root / "product.sqlite3")
    classroom = ClassService(database).create_class("合成测试班")
    sessions = SessionService(database)
    session = sessions.create_session("合成采集考试", classroom.class_id)
    assets = AssetService(database, root / "local_app")
    answer = root / "answer.csv"
    answer.write_text(
        "question,answer,type\n1,A,single_choice\n",
        encoding="utf-8-sig",
    )
    template = root / "template.json"
    template.write_text("{}", encoding="utf-8")
    assets.register(session.session_id, answer, AssetType.ANSWER_KEY)
    assets.register(session.session_id, template, AssetType.TEMPLATE)
    return database, sessions.get_session(session.session_id)


def prepare_web(root: Path):
    web = ProductWebController(root / "local_app")
    classroom = web.facade.create_class("合成测试班")
    session = web.facade.create_session("合成采集考试", classroom.class_id)
    web.facade.add_asset(
        session.session_id,
        "ANSWER_KEY",
        "answer.csv",
        b"question,answer,type\n1,A,single_choice\n",
    )
    web.facade.add_asset(
        session.session_id,
        "TEMPLATE",
        "template.json",
        b"{}",
    )
    return web, web.facade.sessions.get_session(session.session_id)


def mobile_upload(
    web: ProductWebController,
    session_id: str,
    *,
    client_capture_id: str = "capture-test-001",
    content: bytes = JPEG,
    filename: str = "capture.jpg",
    content_type: str = "image/jpeg",
    fields: dict[str, str] | None = None,
):
    values = mobile_fields(client_capture_id)
    if fields:
        values.update(fields)
    return web.post(
        f"/sessions/{session_id}/capture/mobile-web",
        values,
        {"image": UploadedFile(filename, content, content_type)},
    )


def set_session_state(database, session_id: str, state: ExamSessionState) -> None:
    with transaction(database) as connection:
        SessionRepository().update_state(
            connection,
            session_id,
            state,
            utc_now(),
        )
