"""Recognition job orchestration + worker tests (constitution §2 / §14)."""

import unittest
import tempfile
from pathlib import Path

from app.student_recognition.capture.capture_job import CaptureJobStore
from app.student_recognition.common import safe_paths
from app.student_recognition.pipeline.recognition_job import RecognitionJob
from app.student_recognition.pipeline.recognition_worker import RecognitionWorker
from app.student_recognition.state_model import State


class TestRecognitionJob(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        safe_paths.set_captures_root(self.tmp)
        self.store = CaptureJobStore(root=self.tmp)

    def tearDown(self):
        safe_paths.reset_captures_root()

    def test_process_produces_job_and_draft(self):
        rj = RecognitionJob(store=self.store)
        job, draft = rj.process(
            b"image-bytes",
            identity_raw="1李明",
            candidates={"q1": "A"},
            roster={"1": "李明"},
        )
        self.assertEqual(job.status, State.OMR_RECOGNIZED)
        self.assertEqual(draft.status, State.DRAFT_CLEAN)
        self.assertEqual(draft.blocking_errors, [])
        self.assertEqual(draft.review_items, [])

    def test_blocked_draft_when_no_candidates(self):
        rj = RecognitionJob(store=self.store)
        _, draft = rj.process(b"img", identity_raw="1李明", candidates=None, roster={"1": "李明"})
        self.assertEqual(draft.status, State.DRAFT_BLOCKED)
        self.assertIn(ErrorCode_present("OMR_OPTION_CELL_MISSING"), draft.blocking_errors)

    def test_worker_schedules_jobs(self):
        worker = RecognitionWorker(store=self.store)
        worker.enqueue(
            {
                "image_bytes": b"a",
                "identity_raw": "1李明",
                "candidates": {"q1": "A"},
                "roster": {"1": "李明"},
            }
        )
        worker.enqueue(
            {
                "image_bytes": b"b",
                "identity_raw": "2小红",
                "candidates": {"q1": "B"},
                "roster": {"2": "小红"},
            }
        )
        results = worker.run()
        self.assertEqual(len(results), 2)
        self.assertEqual(len(self.store.list_job_ids()), 2)


def ErrorCode_present(name: str):
    from app.student_recognition.errors.error_codes import ErrorCode

    return ErrorCode(name)


if __name__ == "__main__":
    unittest.main()
