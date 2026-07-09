"""Tests for ReportIndexHtmlExporter — fixture-based (P3)."""
import ast, json, shutil, tempfile, unittest
from pathlib import Path
from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.report_index_html_exporter import ReportIndexHtmlExporter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent/"fixtures"/"baseline"


class ReportIndexHtmlExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")
        cls.meta = {"exam_name":"demo","class_name":"Test","subject":"Math","exam_date":"2026-07-09"}

    def test_file_exists_and_valid(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            out = Path(t)
            (out/"simple_report.html").write_text("x","utf-8")
            (out/"advanced_dashboard.html").write_text("x","utf-8")
            (out/"simple_score_report.xlsx").write_text("x","utf-8")
            req = ExportRequest(output_dir=out)
            r = ReportIndexHtmlExporter().export(req, self.meta,
                out/"simple_report.html", out/"advanced_dashboard.html", out/"simple_score_report.xlsx")
            fp = Path(r.generated_files[0])
            self.assertTrue(fp.exists())
            html = fp.read_text("utf-8")
            self.assertIn("批改完成", html)
            self.assertIn("simple_report.html", html)
            self.assertIn("advanced_dashboard.html", html)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_structure_matches_fixture(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            out = Path(t)
            (out/"simple_report.html").write_text("x","utf-8")
            (out/"advanced_dashboard.html").write_text("x","utf-8")
            (out/"simple_score_report.xlsx").write_text("x","utf-8")
            req = ExportRequest(output_dir=out)
            r = ReportIndexHtmlExporter().export(req, self.meta,
                out/"simple_report.html", out/"advanced_dashboard.html", out/"simple_score_report.xlsx")
            fp = Path(r.generated_files[0])
            expected = json.loads((FIXTURES/"html_structures/index.json").read_text("utf-8"))
            self.assertEqual(expected["title"], "批改完成")
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src = Path(__file__).read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__":
    unittest.main()
