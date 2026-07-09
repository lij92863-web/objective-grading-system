"""Workflow integration for infrastructure CSV loaders."""

import shutil
import tempfile
import unittest
from pathlib import Path

from app.workflow import run_grading


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"

CSV_FILES = {
    "summary.csv",
    "detail.csv",
    "item_analysis.csv",
    "knowledge_profile.csv",
    "practice_recommendations.csv",
    "class_report.csv",
    "validation_report.csv",
    "student_report.csv",
}
EXCEL_FILES = {"exam_report.xlsx", "simple_score_report.xlsx"}
HTML_FILES = {"simple_report.html", "advanced_dashboard.html", "index.html"}


class WorkflowLoaderIntegrationTests(unittest.TestCase):
    def test_workflow_demo_outputs_with_infrastructure_loaders(self):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo samples")
        temp_dir = Path(tempfile.mkdtemp(prefix="l7d_", dir=PROJECT_ROOT / "data"))
        try:
            out = temp_dir / "out"
            result = run_grading(
                answer_key_path=DEMO_KEY,
                submissions_path=DEMO_SUB,
                out_dir=out,
                no_archive=True,
            )

            self.assertTrue(result["ok"])
            for filename in CSV_FILES | EXCEL_FILES | HTML_FILES:
                self.assertTrue((out / filename).exists(), filename)
            self.assertEqual(8, len([f for f in CSV_FILES if (out / f).exists()]))
            self.assertEqual(2, len([f for f in EXCEL_FILES if (out / f).exists()]))
            self.assertEqual(3, len([f for f in HTML_FILES if (out / f).exists()]))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
