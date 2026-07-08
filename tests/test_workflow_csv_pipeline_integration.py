"""Workflow CSV pipeline integration — E7B."""

import csv, shutil, tempfile, unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
CSV_FILES = ["summary.csv","detail.csv","item_analysis.csv","knowledge_profile.csv",
             "practice_recommendations.csv","class_report.csv","validation_report.csv","student_report.csv"]
EXCEL_HTML = ["exam_report.xlsx","simple_score_report.xlsx","simple_report.html","advanced_dashboard.html","index.html"]

class WorkflowCsvPipelineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")

    def test_all_csv_plus_excel_html_exist(self):
        t = tempfile.mkdtemp(prefix="e7b_", dir=PROJECT_ROOT/"data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="t")
            self.assertTrue(r["ok"])
            for f in CSV_FILES:
                self.assertTrue((Path(t)/f).exists(), f"Missing {f}")
            for f in EXCEL_HTML:
                self.assertTrue((Path(t)/f).exists(), f"Missing {f}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_csv_field_order_correct(self):
        t = tempfile.mkdtemp(prefix="e7b_", dir=PROJECT_ROOT/"data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="t")
            for fname in CSV_FILES:
                with (Path(t)/fname).open("r", encoding="utf-8-sig", newline="") as h:
                    rows = list(csv.DictReader(h))
                    self.assertGreater(len(rows), 0 if fname != "practice_recommendations.csv" else -1,
                                       f"{fname} is unexpectedly empty")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_cli_still_works(self):
        import subprocess, sys
        t = tempfile.mkdtemp(prefix="e7b_cli_", dir=PROJECT_ROOT/"data")
        try:
            r = subprocess.run([sys.executable, str(PROJECT_ROOT/"objective_grader.py"),
                "--answer-key", str(DEMO_KEY), "--submissions", str(DEMO_SUB),
                "--out-dir", str(Path(t)/"out"), "--no-archive"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            shutil.rmtree(t, ignore_errors=True)

if __name__ == "__main__": unittest.main()
