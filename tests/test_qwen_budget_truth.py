import unittest

from app.recognition.batch_orchestrator import run_synthetic_batch


class QwenBudgetTruthTests(unittest.TestCase):
    def test_budget_exceeded_counts_are_policy_generated(self):
        result = run_synthetic_batch("qwen_budget_exceeded")
        summary = result["batch_summary"]
        self.assertEqual(summary["qwen_call_count"], 2)
        self.assertEqual(summary["blocked_by_budget_count"], 3)
        self.assertEqual(result["qwen_policy_summary"]["blocked_by_budget_count"], 3)
        self.assertEqual(result["review_queue_summary"]["total"], 3)


if __name__ == "__main__":
    unittest.main()
