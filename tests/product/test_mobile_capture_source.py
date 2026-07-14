import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from app.capture import CaptureQueue, CaptureSourceType
from app.capture.mobile_web_camera_source import MobileCaptureError, MobileWebCameraSource

from tests.product.mobile_capture_test_support import JPEG, PNG, mobile_fields, prepare_session


ROOT = Path(__file__).resolve().parents[2]


class MobileCaptureSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.database, self.session = prepare_session(self.root)
        self.queue = CaptureQueue(self.database, self.root / "local_app")
        self.source = MobileWebCameraSource(self.queue)

    def tearDown(self):
        self.temp.cleanup()

    def upload(self, client_id="capture-source-001", content=JPEG, filename="capture.jpg", mime="image/jpeg"):
        fields = mobile_fields(client_id)
        fields["mime_type"] = mime
        return self.source.upload_blob(
            self.session.session_id,
            filename,
            content,
            mime,
            fields,
        )

    def test_valid_jpeg_creates_mobile_source_and_audit_receipt(self):
        result = self.upload()
        self.assertFalse(result.duplicate)
        self.assertEqual(result.job.source_type, CaptureSourceType.MOBILE_WEB_USB_CAMERA)
        self.assertTrue(Path(result.job.stored_image_path).is_file())
        with self.database.connection() as connection:
            receipt = connection.execute("SELECT * FROM mobile_capture_receipts").fetchone()
        self.assertEqual(receipt["client_capture_id"], "capture-source-001")
        self.assertEqual(json.loads(receipt["metadata_json"])["width"], 3840)

    def test_valid_png_creates_capture_job(self):
        result = self.upload(
            client_id="capture-source-png",
            content=PNG,
            filename="capture.png",
            mime="image/png",
        )
        self.assertEqual(result.job.source_type, CaptureSourceType.MOBILE_WEB_USB_CAMERA)

    def test_same_blob_replay_returns_original_job(self):
        first = self.upload("capture-replay-001")
        second = self.upload("capture-replay-002")
        self.assertTrue(second.duplicate)
        self.assertEqual(second.job.capture_job_id, first.job.capture_job_id)
        self.assertEqual(len(self.queue.list_jobs(self.session.session_id)), 1)

    def test_same_client_capture_id_with_different_content_is_blocked(self):
        self.upload("capture-conflict")
        with self.assertRaises(MobileCaptureError) as raised:
            self.upload("capture-conflict", JPEG + b"different")
        self.assertEqual(raised.exception.status, 409)
        self.assertEqual(len(self.queue.list_jobs(self.session.session_id)), 1)

    def test_receipt_database_failure_rolls_back_job_and_removes_image(self):
        with mock.patch.object(
            self.queue,
            "_add_mobile_receipt",
            side_effect=RuntimeError("synthetic receipt failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.upload("capture-db-failure")
        self.assertEqual(self.queue.list_jobs(self.session.session_id), [])
        upload_root = self.root / "local_app" / "uploads" / self.session.session_id
        self.assertEqual(list(upload_root.glob("*")) if upload_root.exists() else [], [])

    def test_file_write_failure_does_not_create_database_record(self):
        with mock.patch.object(Path, "write_bytes", side_effect=OSError("synthetic disk failure")):
            with self.assertRaises(OSError):
                self.upload("capture-file-failure")
        self.assertEqual(self.queue.list_jobs(self.session.session_id), [])


if __name__ == "__main__":
    unittest.main()
