"""Workflow integration after routing analysis rows through builders."""

import shutil
import tempfile
import unittest
from pathlib import Path

from app.workflow import run_grading


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"

REQUIRED_CSV = {
    "summary.csv",
    "detail.csv",
    "item_analysis.csv",
    "knowledge_profile.csv",
    "practice_recommendations.csv",
    "class_report.csv",
    "validation_report.csv",
    "student_report.csv",
}
REQUIRED_EXCEL = {"exam_report.xlsx", "simple_score_report.xlsx"}
REQUIRED_HTML = {"simple_report.html", "advanced_dashboard.html", "index.html"}


class WorkflowAnalysisBuilderIntegrationTests(unittest.TestCase):
    def test_workflow_outputs_core_reports_with_new_analysis_builders(self):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo samples")
        temp_dir = Path(tempfile.mkdtemp(prefix="l5_", dir=PROJECT_ROOT / "data"))
        try:
            out = temp_dir / "out"
            result = run_grading(
                answer_key_path=DEMO_KEY,
                submissions_path=DEMO_SUB,
                out_dir=out,
                no_archive=True,
            )

            self.assertTrue(result["ok"])
            for filename in REQUIRED_CSV | REQUIRED_EXCEL | REQUIRED_HTML:
                self.assertTrue((out / filename).exists(), filename)
            self.assertEqual(
                8,
                len([name for name in REQUIRED_CSV if (out / name).exists()]),
            )
            self.assertEqual(
                2,
                len([name for name in REQUIRED_EXCEL if (out / name).exists()]),
            )
            self.assertEqual(
                3,
                len([name for name in REQUIRED_HTML if (out / name).exists()]),
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
