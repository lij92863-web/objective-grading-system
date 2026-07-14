import json
from pathlib import Path
import tempfile
import unittest

from app.capture.mobile_web_camera_source import MobileWebCameraSource
from app.exam_session.session_model import ExamSessionState
from tests.product.mobile_capture_test_support import (
    JPEG,
    mobile_fields,
    mobile_upload,
    prepare_web,
    set_session_state,
)


ROOT = Path(__file__).resolve().parents[2]


class MobileCaptureStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.web, self.session = prepare_web(self.root)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def payload(response):
        return json.loads(response.body.decode("utf-8"))

    def test_status_counts_mobile_jobs_without_paths_or_student_data(self):
        mobile_upload(self.web, self.session.session_id)
        self.web.facade.capture_upload(
            self.session.session_id,
            "manual.jpg",
            JPEG + b"manual",
        )
        response = self.web.get(f"/sessions/{self.session.session_id}/capture/status.json")
        payload = self.payload(response)
        serialized = response.body.decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertEqual(payload["counts"]["total"], 2)
        self.assertEqual(payload["counts"]["mobile_total"], 1)
        self.assertEqual(payload["counts"]["review_required"], 2)
        self.assertNotIn("stored_image_path", serialized)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("student_no", serialized)

    def test_recent_is_limited_to_twenty_and_bound_to_requested_session(self):
        source = MobileWebCameraSource(self.web.facade.queue)
        for index in range(23):
            fields = mobile_fields(f"capture-status-{index:03d}")
            source.upload_blob(
                self.session.session_id,
                f"capture-{index}.jpg",
                JPEG + str(index).encode("ascii"),
                "image/jpeg",
                fields,
            )
        other = self.web.facade.create_session(
            "未准备的另一场考试",
            self.session.class_id,
        )
        response = self.web.get(f"/sessions/{self.session.session_id}/capture/status.json")
        payload = self.payload(response)
        self.assertEqual(payload["counts"]["total"], 23)
        self.assertEqual(len(payload["recent"]), 20)
        self.assertTrue(all(item["capture_job_id"] for item in payload["recent"]))
        self.assertNotIn(other.session_id, response.body.decode("utf-8"))

    def test_missing_session_status_is_json_404(self):
        response = self.web.get("/sessions/not-found/capture/status.json")
        self.assertEqual(response.status, 404)
        self.assertFalse(self.payload(response)["ok"])

    def test_landing_lists_only_capture_allowed_sessions(self):
        allowed_id = self.session.session_id
        draft = self.web.facade.create_session("未准备考试", self.session.class_id)
        finalized = self.web.facade.create_session("已发布考试", self.session.class_id)
        self.web.facade.add_asset(
            finalized.session_id,
            "ANSWER_KEY",
            "finalized-answer.csv",
            b"question,answer,type\n1,A,single_choice\n",
        )
        self.web.facade.add_asset(
            finalized.session_id,
            "TEMPLATE",
            "finalized-template.json",
            b"{}",
        )
        set_session_state(
            self.web.facade.database,
            finalized.session_id,
            ExamSessionState.FINALIZED,
        )
        page = self.web.get("/mobile-capture").body.decode("utf-8")
        self.assertIn(allowed_id, page)
        self.assertNotIn(draft.session_id, page)
        self.assertNotIn(finalized.session_id, page)


if __name__ == "__main__":
    unittest.main()
