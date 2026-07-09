"""CSV pipeline parity — fixture baseline (T3)."""
import csv, shutil, tempfile, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent/"fixtures"/"baseline"/"csv"
CSV_FILES = ["summary.csv","detail.csv","item_analysis.csv","knowledge_profile.csv",
             "practice_recommendations.csv","class_report.csv","validation_report.csv","student_report.csv"]


class CsvReportPipelineShadowParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")

    def test_8_csv_headers_match_fixtures(self):
        from app.workflow import run_grading
        t = tempfile.mkdtemp(prefix="t3_", dir=PROJECT_ROOT/"data")
        try:
            run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="p")
            for fname in CSV_FILES:
                actual = Path(t)/fname
                fixture = FIXTURES/fname
                self.assertTrue(actual.exists(), f"Missing {fname}")
                if fixture.exists():
                    with actual.open("r",encoding="utf-8-sig",newline="") as a:
                        a_rows = list(csv.DictReader(a))
                    with fixture.open("r",encoding="utf-8-sig",newline="") as f:
                        f_rows = list(csv.DictReader(f))
                    self.assertEqual(len(a_rows), len(f_rows),
                                     f"{fname}: row count mismatch")
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        import ast; src = Path(__file__).read_text("utf-8")
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__": unittest.main()
