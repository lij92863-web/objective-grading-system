"""Excel shadow parity — fixture baseline (T3)."""
import json, shutil, tempfile, unittest, zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent/"fixtures"/"baseline"/"xlsx_structures"


class ExcelShadowParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")

    def test_excel_structure_matches_fixtures(self):
        from app.workflow import run_grading
        t = tempfile.mkdtemp(prefix="t3_", dir=PROJECT_ROOT/"data")
        try:
            run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="p")
            for fname in ["exam_report.xlsx","simple_score_report.xlsx"]:
                fp = Path(t)/fname
                self.assertTrue(fp.exists()); self.assertTrue(zipfile.is_zipfile(fp))
                self.assertGreater(fp.stat().st_size, 1000)
                fix = FIXTURES/fname.replace(".xlsx",".json")
                if fix.exists():
                    expected = json.loads(fix.read_text("utf-8"))
                    from tests.helpers.baseline_fixtures import normalize_xlsx_structure
                    actual = normalize_xlsx_structure(fp)
                    self.assertEqual(actual["sheet_names"], expected["sheet_names"],
                                     f"{fname}: sheet name mismatch")
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        import ast; src = Path(__file__).read_text("utf-8")
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__": unittest.main()
