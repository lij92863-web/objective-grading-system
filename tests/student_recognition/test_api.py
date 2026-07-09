"""Thin API surface tests (constitution §14: API stays thin, no algorithms)."""

import unittest
import tempfile
from pathlib import Path

from app.student_recognition.api import SREApi, create_blueprint
from app.student_recognition.capture.capture_job import CaptureJobStore
from app.student_recognition.common import safe_paths
from app.student_recognition.pipeline.recognition_job import RecognitionJob
from app.student_recognition.review.review_item import ReviewStatus


class TestSREApi(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        safe_paths.set_captures_root(self.tmp)
        self.api = SREApi(root=self.tmp)

    def tearDown(self):
        safe_paths.reset_captures_root()

    def test_upload_returns_summary(self):
        out = self.api.upload(
            b"img",
            identity_raw="1李明",
            candidates={"q1": "A"},
            roster={"1": "李明"},
        )
        self.assertIn("job_id", out)
        self.assertEqual(out["draft_status"], "draft_clean")
        self.assertEqual(out["blocking_errors"], [])
        self.assertEqual(out["review_items"], [])

    def test_get_job_and_list(self):
        self.api.upload(b"img", identity_raw="1李明", candidates={"q1": "A"}, roster={"1": "李明"})
        jobs = self.api.list_jobs()
        self.assertEqual(len(jobs), 1)
        info = self.api.get_job(jobs[0])
        self.assertEqual(info["status"], "omr_recognized")

    def test_resolve_review_via_queue(self):
        store = CaptureJobStore(root=self.tmp)
        rj = RecognitionJob(store=store)
        _, draft = rj.process(
            b"img", identity_raw="李明", candidates={"q1": "A"}, roster={"1": "李明"}
        )
        queue = self.api.review_queue_from_draft(draft)
        self.assertTrue(queue.has_unresolved())
        item = queue.all()[0]
        self.api.resolve_review(queue, item.item_id, ReviewStatus.RESOLVED, note="ok", by="teacher")
        self.assertFalse(queue.has_unresolved())

    def test_blueprint_none_without_flask(self):
        # Flask is optional; engine must import and run without it.
        self.assertIsNone(create_blueprint())


if __name__ == "__main__":
    unittest.main()
