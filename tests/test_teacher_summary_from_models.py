import unittest

from app.recognition.batch_orchestrator import run_synthetic_batch
from app.recognition.batch_summary import BatchRecognitionSummary
from app.recognition.teacher_facing_summary import TeacherFacingSummary


class TeacherSummaryFromModelsTests(unittest.TestCase):
    def test_summary_uses_model_counts(self):
        batch = run_synthetic_batch("qwen_budget_exceeded")
        summary = TeacherFacingSummary.from_models(
            BatchRecognitionSummary(**batch["batch_summary"]),
            batch["review_queue_summary"],
            {"total_students": batch["images"], "total_items": batch["total_items"]},
            batch["qwen_cost"],
            student_statuses=batch["student_statuses"],
        )
        self.assertEqual(summary.needs_review_students, 2)
        self.assertEqual(summary.ready_students, 0)


if __name__ == "__main__":
    unittest.main()
