import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tests.product.mobile_capture_test_support import (
    JPEG,
    PNG,
    mobile_upload,
    prepare_web,
)


ROOT = Path(__file__).resolve().parents[2]


class MobileCaptureApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.web, self.session = prepare_web(self.root)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def payload(response):
        return json.loads(response.body.decode("utf-8"))

    def test_jpeg_returns_json_job_and_invokes_conservative_pipeline(self):
        pipeline = self.web.facade.mobile_capture.pipeline
        with mock.patch.object(pipeline, "process_mock", wraps=pipeline.process_mock) as process:
            response = mobile_upload(self.web, self.session.session_id)
        payload = self.payload(response)
        self.assertEqual(response.status, 201)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["duplicate"])
        self.assertEqual(payload["state"], "QUEUED")
        self.assertTrue(payload["capture_job_id"])
        self.assertNotIn("Location", response.headers)
        process.assert_called_once()

    def test_png_returns_created_json(self):
        response = mobile_upload(
            self.web,
            self.session.session_id,
            client_capture_id="capture-api-png",
            content=PNG,
            filename="capture.png",
            content_type="image/png",
            fields={"mime_type": "image/png"},
        )
        self.assertEqual(response.status, 201)
        self.assertTrue(self.payload(response)["capture_job_id"])

    def test_lost_response_replay_is_idempotent(self):
        first = mobile_upload(self.web, self.session.session_id, client_capture_id="capture-replay")
        second = mobile_upload(self.web, self.session.session_id, client_capture_id="capture-replay")
        first_payload = self.payload(first)
        second_payload = self.payload(second)
        self.assertEqual(second.status, 200)
        self.assertTrue(second_payload["duplicate"])
        self.assertEqual(second_payload["capture_job_id"], first_payload["capture_job_id"])
        self.assertEqual(len(self.web.facade.queue.list_jobs(self.session.session_id)), 1)

    def test_missing_image_returns_json_400(self):
        response = self.web.post(
            f"/sessions/{self.session.session_id}/capture/mobile-web",
            {},
            {},
        )
        self.assertEqual(response.status, 400)
        self.assertFalse(self.payload(response)["ok"])

    def test_pipeline_failure_keeps_registered_job_and_reports_failed_status(self):
        with mock.patch.object(
            self.web.facade.mobile_capture.pipeline,
            "process_mock",
            side_effect=RuntimeError("synthetic pipeline failure"),
        ):
            response = mobile_upload(
                self.web,
                self.session.session_id,
                client_capture_id="capture-pipeline-failure",
                content=JPEG + b"pipeline",
            )
        payload = self.payload(response)
        self.assertEqual(response.status, 201)
        self.assertTrue(payload["ok"])
        self.assertIn("处理失败", payload["warning"])
        status = self.payload(
            self.web.get(f"/sessions/{self.session.session_id}/capture/status.json")
        )
        self.assertEqual(status["counts"]["failed"], 1)
        self.assertEqual(len(self.web.facade.queue.list_jobs(self.session.session_id)), 1)


if __name__ == "__main__":
    unittest.main()
