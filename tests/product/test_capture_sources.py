import tempfile
import unittest
from pathlib import Path

from app.capture import CaptureQueue, CaptureSourceType
from app.capture.browser_camera_source import BrowserCameraSource
from app.capture.camera_probe import probe_system_camera
from app.capture.upload_source import ManualUploadSource
from app.capture.watched_folder_source import WatchedFolderSource
from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.storage import LocalDatabase


ROOT = Path(__file__).resolve().parents[2]
PNG = b"\x89PNG\r\n\x1a\nsynthetic-product-test"


class CaptureSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.database = LocalDatabase(self.root / "product.sqlite3")
        classroom = ClassService(self.database).create_class("高一 3 班")
        self.sessions = SessionService(self.database)
        self.session = self.sessions.create_session("期中考试", classroom.class_id)
        assets = AssetService(self.database, self.root / "local_app")
        answer = self.root / "answer.csv"
        answer.write_text(
            "question,answer,type\n1,A,single_choice\n",
            encoding="utf-8-sig",
        )
        template = self.root / "template.json"
        template.write_text("{}", encoding="utf-8")
        assets.register(self.session.session_id, answer, AssetType.ANSWER_KEY)
        assets.register(self.session.session_id, template, AssetType.TEMPLATE)
        self.queue = CaptureQueue(self.database, self.root / "local_app")

    def tearDown(self):
        self.temp.cleanup()

    def test_manual_upload_creates_capture_job_and_deduplicates(self):
        image = self.root / "image.png"
        image.write_bytes(PNG)
        source = ManualUploadSource(self.queue)
        first = source.upload(self.session.session_id, image)
        second = source.upload(self.session.session_id, image)
        self.assertEqual(first.job.source_type, CaptureSourceType.MANUAL_UPLOAD)
        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(len(self.queue.list_jobs(self.session.session_id)), 1)

    def test_non_image_file_rejected(self):
        path = self.root / "not-image.txt"
        path.write_text("x", encoding="utf-8")
        with self.assertRaises(ValueError):
            ManualUploadSource(self.queue).upload(self.session.session_id, path)

    def test_watched_folder_missing_blocks_and_detects_new_image(self):
        source = WatchedFolderSource(self.queue)
        with self.assertRaises(ValueError):
            source.scan(self.session.session_id, self.root / "missing")
        folder = self.root / "watch"
        folder.mkdir()
        (folder / "one.jpg").write_bytes(PNG + b"one")
        (folder / "ignore.txt").write_text("ignore", encoding="utf-8")
        first = source.scan(self.session.session_id, folder)
        second = source.scan(self.session.session_id, folder)
        self.assertEqual(len(first.created), 1)
        self.assertEqual(second.duplicate_count, 1)

    def test_browser_camera_upload_creates_job(self):
        result = BrowserCameraSource(self.queue).upload_blob(
            self.session.session_id,
            "camera.jpg",
            PNG + b"camera",
        )
        self.assertEqual(result.job.source_type, CaptureSourceType.BROWSER_CAMERA)

    def test_capture_rejected_when_session_not_capture_ready(self):
        classroom = ClassService(self.database).create_class("高一 4 班")
        draft = self.sessions.create_session("未准备", classroom.class_id)
        with self.assertRaises(ValueError):
            self.queue.add_bytes(
                draft.session_id,
                "image.png",
                PNG,
                CaptureSourceType.MANUAL_UPLOAD,
            )

    def test_camera_probe_unavailable_is_graceful(self):
        result = probe_system_camera()
        self.assertFalse(result.available)
        self.assertIn("浏览器", result.message)


if __name__ == "__main__":
    unittest.main()
