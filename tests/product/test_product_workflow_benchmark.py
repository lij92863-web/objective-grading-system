import copy
import tempfile
import unittest
from pathlib import Path

from scripts.product.product_workflow_oracle import compare_final_scores
from scripts.product.run_product_workflow_benchmark import run_benchmark


ROOT = Path(__file__).resolve().parents[2]


class ProductWorkflowOracleTests(unittest.TestCase):
    def setUp(self):
        self.expected = [
            {
                "student_id": "student-a",
                "student_no": "001",
                "student_name": "Student 001",
                "score": 1.0,
                "max_score": 2.0,
                "percent": 50.0,
                "included": True,
            },
            {
                "student_id": "student-b",
                "student_no": "002",
                "student_name": "Student 002",
                "score": 2.0,
                "max_score": 2.0,
                "percent": 100.0,
                "included": True,
            },
        ]
        self.actual = copy.deepcopy(self.expected)

    def test_correct_content_has_zero_wrong_finalized(self):
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_student_number_tampering(self):
        self.actual[0]["student_no"] = "999"
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["wrong_student_binding_count"], 1)
        self.assertGreater(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_score_tampering(self):
        self.actual[0]["score"] = 0.0
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["wrong_score_count"], 1)
        self.assertGreater(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_swapped_student_scores(self):
        self.actual[0]["score"], self.actual[1]["score"] = (
            self.actual[1]["score"],
            self.actual[0]["score"],
        )
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["wrong_score_count"], 2)
        self.assertGreater(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_missing_student(self):
        metrics = compare_final_scores(self.expected, self.actual[:-1])
        self.assertEqual(metrics["missing_final_score_count"], 1)
        self.assertGreater(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_unexpected_student(self):
        self.actual.append({
            "student_id": "outsider",
            "student_no": "999",
            "student_name": "Outsider",
            "score": 2.0,
            "max_score": 2.0,
            "percent": 100.0,
        })
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["unexpected_final_score_count"], 1)
        self.assertGreater(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_score_above_maximum(self):
        self.actual[0]["score"] = 2.5
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["invalid_score_range_count"], 1)
        self.assertGreater(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_percent_above_100(self):
        self.actual[0]["percent"] = 150.0
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["invalid_score_range_count"], 1)
        self.assertGreater(metrics["wrong_finalized_count"], 0)

    def test_oracle_detects_duplicate_capture_result(self):
        self.actual.append(copy.deepcopy(self.actual[0]))
        metrics = compare_final_scores(self.expected, self.actual)
        self.assertEqual(metrics["duplicate_final_score_count"], 1)
        self.assertGreater(metrics["wrong_finalized_count"], 0)


class ProductWorkflowBenchmarkTests(unittest.TestCase):
    def test_benchmark_uses_52_captures_and_content_truth(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as temporary:
            metrics = run_benchmark(Path(temporary))
        self.assertEqual(metrics["capture_job_count"], 52)
        self.assertEqual(metrics["excluded_duplicate_capture_count"], 2)
        self.assertEqual(metrics["actual_final_score_count"], 50)
        self.assertEqual(metrics["wrong_finalized_count"], 0)


if __name__ == "__main__":
    unittest.main()
