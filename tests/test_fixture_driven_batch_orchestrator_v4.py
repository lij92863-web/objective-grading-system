import unittest

from app.recognition.batch_orchestrator import run_synthetic_batch
from app.recognition.synthetic_batch_loader import load_all_fixtures


class FixtureDrivenBatchOrchestratorV4Tests(unittest.TestCase):
    def test_all_fixtures_match_expected_projection(self):
        for fixture in load_all_fixtures():
            result = run_synthetic_batch(scenario=fixture.scenario)
            actual = {
                "batch_status": result["status"],
                "total_students": result["images"],
                "total_items": result["total_items"],
                "auto_accepted_items": result["batch_summary"]["auto_accepted_items"],
                "needs_review_items": result["batch_summary"]["needs_review_items"],
                "blocking_items": result["batch_summary"]["blocking_items"],
                "qwen_call_count": result["batch_summary"]["qwen_call_count"],
                "blocked_by_budget_count": result["batch_summary"]["blocked_by_budget_count"],
                "ready_students": sum(1 for v in result["student_statuses"].values() if v == "ready"),
                "needs_review_students": sum(1 for v in result["student_statuses"].values() if v == "needs_review"),
                "blocked_students": sum(1 for v in result["student_statuses"].values() if v == "blocked"),
            }
            self.assertEqual(actual, fixture.expected)

    def test_unknown_scenario_fails_closed(self):
        with self.assertRaises(ValueError):
            run_synthetic_batch("unknown")


if __name__ == "__main__":
    unittest.main()
