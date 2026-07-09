"""Workflow HTML exporter integration — E4G."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"

CSV_FILES = ["summary.csv", "detail.csv", "item_analysis.csv",
             "knowledge_profile.csv", "practice_recommendations.csv",
             "class_report.csv", "validation_report.csv", "student_report.csv"]
EXCEL_FILES = ["exam_report.xlsx", "simple_score_report.xlsx"]
HTML_FILES = ["simple_report.html", "advanced_dashboard.html", "index.html"]


class WorkflowHtmlExporterIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def test_workflow_runs_ok(self):
        t = tempfile.mkdtemp(prefix="e4g_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                            no_archive=True, exam_name="x")
            self.assertTrue(r["ok"], f"Workflow failed: {r}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_csv_files_exist(self):
        t = tempfile.mkdtemp(prefix="e4g_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            for f in CSV_FILES:
                self.assertTrue((Path(t) / f).exists(), f"Missing {f}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_excel_files_exist(self):
        t = tempfile.mkdtemp(prefix="e4g_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            for f in EXCEL_FILES:
                self.assertTrue((Path(t) / f).exists(), f"Missing {f}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_html_files_exist(self):
        t = tempfile.mkdtemp(prefix="e4g_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            for f in HTML_FILES:
                self.assertTrue((Path(t) / f).exists(), f"Missing {f}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_html_titles_correct(self):
        t = tempfile.mkdtemp(prefix="e4g_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            sr = (Path(t) / "simple_report.html").read_text("utf-8")
            self.assertIn("普通版报告", sr)
            ad = (Path(t) / "advanced_dashboard.html").read_text("utf-8")
            self.assertIn("高级学情分析报告", ad)
            idx = (Path(t) / "index.html").read_text("utf-8")
            self.assertIn("批改完成", idx)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_html_links_correct(self):
        t = tempfile.mkdtemp(prefix="e4g_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            idx = (Path(t) / "index.html").read_text("utf-8")
            self.assertIn("simple_report.html", idx)
            self.assertIn("advanced_dashboard.html", idx)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_old_cli_smoke(self):
        t = tempfile.mkdtemp(prefix="e4g_cli_", dir=PROJECT_ROOT / "data")
        try:
            r = subprocess.run([
                sys.executable,
                str(PROJECT_ROOT / "objective_grader.py"),
                "--answer-key", str(DEMO_KEY),
                "--submissions", str(DEMO_SUB),
                "--out-dir", str(Path(t) / "out"),
                "--no-archive",
            ], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0,
                             f"CLI failed:\n{r.stderr}")
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
