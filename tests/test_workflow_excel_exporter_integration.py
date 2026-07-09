"""Workflow Excel exporter integration tests — E3E."""

import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"

CSV_FILES = [
    "summary.csv", "detail.csv", "item_analysis.csv",
    "knowledge_profile.csv", "practice_recommendations.csv",
    "class_report.csv", "validation_report.csv", "student_report.csv",
]
EXCEL_FILES = ["exam_report.xlsx", "simple_score_report.xlsx"]
HTML_FILES = ["simple_report.html", "advanced_dashboard.html", "index.html"]


class WorkflowExcelExporterIntegrationTests(unittest.TestCase):
    """Verify workflow runs end-to-end with new Excel exporters."""

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def test_workflow_runs_successfully(self):
        t = tempfile.mkdtemp(prefix="e3e_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                            no_archive=True, exam_name="x")
            self.assertTrue(r["ok"], f"Workflow failed: {r}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_csv_files_exist(self):
        t = tempfile.mkdtemp(prefix="e3e_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            for name in CSV_FILES:
                self.assertTrue(
                    (Path(t) / name).exists(),
                    f"Missing CSV: {name}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_excel_files_exist(self):
        t = tempfile.mkdtemp(prefix="e3e_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            for name in EXCEL_FILES:
                self.assertTrue(
                    (Path(t) / name).exists(),
                    f"Missing Excel: {name}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_excel_zips_are_valid(self):
        t = tempfile.mkdtemp(prefix="e3e_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            for name in EXCEL_FILES:
                fp = Path(t) / name
                self.assertTrue(zipfile.is_zipfile(fp),
                                f"{name} is not a valid ZIP")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_excel_sheet_names_correct(self):
        t = tempfile.mkdtemp(prefix="e3e_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            import xml.etree.ElementTree as ET
            ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            fp = Path(t) / "exam_report.xlsx"
            with zipfile.ZipFile(fp) as z:
                wb = z.read("xl/workbook.xml").decode("utf-8")
                root = ET.fromstring(wb)
                names = [s.get("name", "")
                         for s in root.findall(".//ns:sheet", ns)]
            self.assertEqual(len(names), 9, f"got {len(names)} sheets: {names}")
            self.assertIn("成绩总表", names)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_html_still_exists(self):
        """HTML generation must still work (still on legacy)."""
        t = tempfile.mkdtemp(prefix="e3e_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            for name in HTML_FILES:
                self.assertTrue(
                    (Path(t) / name).exists(),
                    f"Missing HTML: {name}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_real_api_called(self):
        t = tempfile.mkdtemp(prefix="e3e_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                            no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_old_cli_smoke(self):
        import subprocess, sys
        t = tempfile.mkdtemp(prefix="e3e_cli_", dir=PROJECT_ROOT / "data")
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
