"""R96: Batch recognition acceptance tests."""
import json, subprocess, sys, unittest
from pathlib import Path
from app.recognition.batch_job import RecognitionBatchJob
from app.recognition.batch_summary import count_from_decisions
from app.recognition.contracts import RecognitionDecision

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class BatchRecognitionAcceptanceTests(unittest.TestCase):
    def test_job_created(self):
        j = RecognitionBatchJob(job_id="j1")
        self.assertEqual(j.status, "created")

    def test_job_completed(self):
        j = RecognitionBatchJob(job_id="j1")
        self.assertTrue(j.transition("running"))
        self.assertTrue(j.transition("completed"))
        self.assertEqual(j.status, "completed")

    def test_invalid_transition_rejected(self):
        j = RecognitionBatchJob(job_id="j1")
        self.assertFalse(j.transition("completed"))

    def test_completed_with_review(self):
        j = RecognitionBatchJob(job_id="j1")
        j.transition("running")
        decs = [[RecognitionDecision(question_number=1, needs_review=True, reason="conflict")]]
        s = count_from_decisions(decs)
        self.assertGreater(s.needs_review_items, 0)
        j.transition("completed_with_review")

    def test_batch_with_blocking(self):
        j = RecognitionBatchJob(job_id="j1")
        j.transition("running")
        decs = [[RecognitionDecision(question_number=1, blocking=True, reason="identity_conflict")]]
        s = count_from_decisions(decs)
        self.assertGreater(s.blocking_items, 0)
        j.transition("blocked")
        self.assertEqual(j.status, "blocked")

    def test_synthetic_batch_cli(self):
        r = subprocess.run([sys.executable,
            str(PROJECT_ROOT/"scripts/run_synthetic_batch_recognition.py"), "--count", "3"],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(len(data["images"]), 3)

    def test_evaluate_synthetic_cli(self):
        r = subprocess.run([sys.executable,
            str(PROJECT_ROOT/"scripts/evaluate_synthetic_batch.py")],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__": unittest.main()
