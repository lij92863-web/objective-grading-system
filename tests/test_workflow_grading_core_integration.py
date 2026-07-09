import shutil
import tempfile
import unittest
from pathlib import Path

from legacy import objective_grader_legacy as legacy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
EXPECTED_FILES = [
    "summary.csv",
    "detail.csv",
    "item_analysis.csv",
    "knowledge_profile.csv",
    "practice_recommendations.csv",
    "class_report.csv",
    "validation_report.csv",
    "student_report.csv",
    "exam_report.xlsx",
    "simple_score_report.xlsx",
    "simple_report.html",
    "advanced_dashboard.html",
    "index.html",
]


class WorkflowGradingCoreIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists() or not DEMO_SUB.exists():
            raise unittest.SkipTest("demo samples are unavailable")

    def test_workflow_runs_without_legacy_grade_all(self):
        from app.workflow import run_grading

        original_grade_all = legacy.grade_all

        def fail_if_called(*args, **kwargs):
            raise AssertionError("workflow must not call legacy.grade_all")

        temp_dir = Path(tempfile.mkdtemp(prefix="l10b_workflow_", dir=PROJECT_ROOT / "data"))
        try:
            legacy.grade_all = fail_if_called
            out_dir = temp_dir / "out"
            result = run_grading(DEMO_KEY, DEMO_SUB, out_dir, no_archive=True, exam_name="l10b")
            self.assertTrue(result["ok"])
            for filename in EXPECTED_FILES:
                self.assertTrue((out_dir / filename).exists(), filename)
        finally:
            legacy.grade_all = original_grade_all
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
