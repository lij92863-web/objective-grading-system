"""Excel legacy behavior lock — E8A. No migration, just audit."""

import shutil, tempfile, unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class ExcelLegacyBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")

    def test_excel_files_exist_and_non_empty(self):
        t = tempfile.mkdtemp(prefix="e8a_", dir=PROJECT_ROOT/"data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="x")
            xlsx = Path(t)/"exam_report.xlsx"
            self.assertTrue(xlsx.exists())
            self.assertGreater(xlsx.stat().st_size, 1000)
            simple = Path(t)/"simple_score_report.xlsx"
            self.assertTrue(simple.exists())
            self.assertGreater(simple.stat().st_size, 1000)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_excel_opens_with_openpyxl(self):
        t = tempfile.mkdtemp(prefix="e8a_", dir=PROJECT_ROOT/"data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="x")
            try:
                from openpyxl import load_workbook
                wb = load_workbook(Path(t)/"exam_report.xlsx", read_only=True)
                sheets = wb.sheetnames
                self.assertGreater(len(sheets), 1, f"Excel has {len(sheets)} sheets")
                wb.close()
            except ImportError:
                self.skipTest("openpyxl not available")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_api_called(self):
        t = tempfile.mkdtemp(prefix="e8a_", dir=PROJECT_ROOT/"data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
        finally:
            shutil.rmtree(t, ignore_errors=True)

if __name__ == "__main__": unittest.main()
