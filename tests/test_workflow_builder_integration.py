"""Workflow builder integration — fixture baseline (T5)."""
import csv, shutil, tempfile, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
EXPECTED_FILES = ["summary.csv","detail.csv","item_analysis.csv","knowledge_profile.csv",
    "practice_recommendations.csv","class_report.csv","validation_report.csv","student_report.csv",
    "exam_report.xlsx","simple_score_report.xlsx","simple_report.html",
    "advanced_dashboard.html","index.html"]


class WorkflowBuilderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")

    def test_workflow_produces_all_outputs(self):
        from app.workflow import run_grading
        t = tempfile.mkdtemp(prefix="t5_", dir=PROJECT_ROOT/"data")
        try:
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
            for f in EXPECTED_FILES:
                self.assertTrue((Path(t)/f).exists(), f"Missing {f}")
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        import ast; src = Path(__file__).read_text("utf-8")
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__": unittest.main()
