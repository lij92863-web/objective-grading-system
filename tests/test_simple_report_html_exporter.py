"""Tests for SimpleReportHtmlExporter — fixture-based (P3)."""
import ast, json, shutil, tempfile, unittest
from pathlib import Path
from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.simple_report_html_exporter import SimpleReportHtmlExporter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent/"fixtures"/"baseline"


class SimpleReportHtmlExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")
        from app.compat.objective_grader_compat import load_answer_key, load_submissions, grade_all, simple_score_rows, item_stats
        ak = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, ak)
        cls.results = grade_all(ak, subs)
        cls.simple_rows = simple_score_rows(cls.results)
        cls.item_rows = item_stats(ak, cls.results)
        cls.meta = {"exam_name":"demo","class_name":"Test","subject":"Math","exam_date":"2026-07-09"}

    def test_file_exists_and_valid(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            req = ExportRequest(output_dir=Path(t))
            r = SimpleReportHtmlExporter().export(req, self.meta, self.results, self.simple_rows, self.item_rows)
            fp = Path(r.generated_files[0])
            self.assertTrue(fp.exists())
            self.assertGreater(fp.stat().st_size, 500)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_structure_matches_fixture(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            req = ExportRequest(output_dir=Path(t))
            r = SimpleReportHtmlExporter().export(req, self.meta, self.results, self.simple_rows, self.item_rows)
            fp = Path(r.generated_files[0])
            expected = json.loads((FIXTURES/"html_structures/simple_report.json").read_text("utf-8"))
            self.assertIn("普通版报告", expected["title"])
            self.assertIn("学生成绩表", expected["sections"])
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
            self.assertTrue((Path(t)/"simple_report.html").exists())
        finally: shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
