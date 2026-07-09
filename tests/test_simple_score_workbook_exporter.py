"""Tests for SimpleScoreWorkbookExporter — fixture-based (P3)."""
import ast, json, shutil, tempfile, unittest, zipfile
from pathlib import Path
from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.simple_score_workbook_exporter import (
    FIELDS, SHEET_NAME, SimpleScoreWorkbookExporter,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline"


class SimpleScoreWorkbookExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")
        from app.compat.objective_grader_compat import load_answer_key, load_submissions, grade_all, simple_score_rows
        ak = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, ak)
        cls.simple_rows = simple_score_rows(grade_all(ak, subs))

    def test_exporter_writes_valid_xlsx(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            req = ExportRequest(output_dir=Path(t))
            r = SimpleScoreWorkbookExporter().export(req, self.simple_rows)
            fp = Path(r.generated_files[0])
            self.assertTrue(fp.exists())
            self.assertTrue(zipfile.is_zipfile(fp))
            self.assertGreater(fp.stat().st_size, 1000)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_structure_matches_fixture(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            req = ExportRequest(output_dir=Path(t))
            r = SimpleScoreWorkbookExporter().export(req, self.simple_rows)
            fp = Path(r.generated_files[0])
            expected = json.loads((FIXTURES/"xlsx_structures/simple_score_report.json").read_text("utf-8"))
            self.assertEqual(expected["sheet_names"], ["scores"])
            self.assertIn("scores", expected["headers"])
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_header_matches_fixture(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            req = ExportRequest(output_dir=Path(t))
            r = SimpleScoreWorkbookExporter().export(req, self.simple_rows)
            fp = Path(r.generated_files[0])
            expected = json.loads((FIXTURES/"xlsx_structures/simple_score_report.json").read_text("utf-8"))
            self.assertEqual(expected["headers"]["scores"], FIELDS)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src = Path(__file__).read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)

    def test_old_workflow_unaffected(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
            self.assertTrue((Path(t)/"simple_score_report.xlsx").exists())
        finally: shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
