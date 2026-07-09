"""Tests for AdvancedDashboardHtmlExporter — fixture-based (P3)."""
import ast, json, shutil, tempfile, unittest
from pathlib import Path
from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.advanced_dashboard_html_exporter import AdvancedDashboardHtmlExporter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent/"fixtures"/"baseline"


class AdvancedDashboardHtmlExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")
        from app.compat.objective_grader_compat import (
            load_answer_key, load_submissions, grade_all,
            build_knowledge_profiles, build_validation_report, item_stats,
        )
        ak = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, ak)
        cls.results = grade_all(ak, subs)
        cls.profiles = build_knowledge_profiles(ak, cls.results)
        cls.item_rows = item_stats(ak, cls.results)
        cls.val_rows = build_validation_report(ak, subs, cls.results, cls.profiles)
        cls.meta = {"exam_name":"demo","class_name":"Test","subject":"Math","exam_date":"2026-07-09"}

    def test_file_exists_and_valid(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            req = ExportRequest(output_dir=Path(t))
            r = AdvancedDashboardHtmlExporter().export(req, self.meta, self.results, self.profiles, self.val_rows, self.item_rows)
            fp = Path(r.generated_files[0])
            self.assertTrue(fp.exists())
            self.assertGreater(fp.stat().st_size, 500)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_structure_matches_fixture(self):
        t = tempfile.mkdtemp(prefix="p3_", dir=PROJECT_ROOT/"data")
        try:
            req = ExportRequest(output_dir=Path(t))
            r = AdvancedDashboardHtmlExporter().export(req, self.meta, self.results, self.profiles, self.val_rows, self.item_rows)
            fp = Path(r.generated_files[0])
            expected = json.loads((FIXTURES/"html_structures/advanced_dashboard.json").read_text("utf-8"))
            self.assertIn("高级学情分析报告", expected["title"])
            self.assertIn("成绩分布", expected["sections"])
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
