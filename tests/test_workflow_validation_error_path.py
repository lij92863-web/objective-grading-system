import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from legacy import objective_grader_legacy as legacy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
CSV_FILES = [
    "summary.csv",
    "detail.csv",
    "item_analysis.csv",
    "knowledge_profile.csv",
    "practice_recommendations.csv",
    "class_report.csv",
    "validation_report.csv",
    "student_report.csv",
]
EXCEL_FILES = ["exam_report.xlsx", "simple_score_report.xlsx"]
HTML_FILES = ["simple_report.html", "advanced_dashboard.html", "index.html"]


class WorkflowValidationErrorPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists() or not DEMO_SUB.exists():
            raise unittest.SkipTest("demo samples are unavailable")

    def _read_validation_rows(self, path):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_blocking_error_path_uses_new_writer(self):
        from app.workflow import run_grading

        temp_dir = Path(tempfile.mkdtemp(prefix="l8c_blocked_", dir=PROJECT_ROOT / "data"))
        original_writer = legacy.write_validation_report

        def fail_if_called(*args, **kwargs):
            raise AssertionError("legacy.write_validation_report must not be called")

        try:
            legacy.write_validation_report = fail_if_called
            out_dir = temp_dir / "out"
            result = run_grading(
                DEMO_KEY,
                DEMO_SUB,
                out_dir,
                no_archive=True,
                exam_name="l8c",
                extra_validation_rows=[
                    {
                        "severity": "error",
                        "scope": "input",
                        "item": "manual",
                        "message": "forced blocking error",
                    }
                ],
            )

            self.assertFalse(result["ok"])
            self.assertTrue(result["blocked"])
            self.assertTrue((out_dir / "validation_report.csv").exists())
            self.assertTrue((out_dir / "error_report.html").exists())
            messages = [row["message"] for row in self._read_validation_rows(out_dir / "validation_report.csv")]
            self.assertIn("forced blocking error", messages)
        finally:
            legacy.write_validation_report = original_writer
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_success_path_outputs_are_unchanged(self):
        from app.workflow import run_grading

        temp_dir = Path(tempfile.mkdtemp(prefix="l8c_success_", dir=PROJECT_ROOT / "data"))
        try:
            out_dir = temp_dir / "out"
            result = run_grading(DEMO_KEY, DEMO_SUB, out_dir, no_archive=True, exam_name="l8c")
            self.assertTrue(result["ok"])
            for filename in CSV_FILES + EXCEL_FILES + HTML_FILES:
                self.assertTrue((out_dir / filename).exists(), filename)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
