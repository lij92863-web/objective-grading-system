"""Tests for ReportIndexHtmlExporter — E4E."""

import ast
import shutil
import tempfile
import unittest
from pathlib import Path

from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.report_index_html_exporter import (
    ReportIndexHtmlExporter,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class ReportIndexHtmlExporterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _generate_both(self):
        t = tempfile.mkdtemp(prefix="e4e_", dir=PROJECT_ROOT / "data")
        try:
            import legacy.objective_grader_legacy as leg
            ak = leg.load_answer_key(DEMO_KEY)
            subs = leg.load_submissions(DEMO_SUB, ak)
            results = leg.grade_all(ak, subs)
            profiles = leg.build_knowledge_profiles(ak, results)
            item_rows = leg.item_stats(ak, results)
            simple_rows = leg.simple_score_rows(results)
            validation_rows = leg.build_validation_report(
                ak, subs, results, profiles)
            meta_obj = leg.ExamMeta(exam_name="demo", class_name="Test",
                                    subject="Math", exam_date="2026-07-09")

            leg_dir = Path(t) / "legacy"
            leg_dir.mkdir()
            leg.write_simple_score_workbook(
                leg_dir / "simple_score_report.xlsx", simple_rows)
            leg.write_simple_report(
                leg_dir / "simple_report.html", meta_obj, ak,
                results, simple_rows, item_rows)
            leg.write_advanced_dashboard(
                leg_dir / "advanced_dashboard.html", meta_obj,
                results, profiles, validation_rows, item_rows)
            leg.write_report_index(
                leg_dir / "index.html", meta_obj,
                leg_dir / "simple_report.html",
                leg_dir / "advanced_dashboard.html",
                leg_dir / "simple_score_report.xlsx")

            # New exporter
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            # Need the files to exist for report_link
            (new_dir / "simple_report.html").write_text("x", encoding="utf-8")
            (new_dir / "advanced_dashboard.html").write_text("x", encoding="utf-8")
            (new_dir / "simple_score_report.xlsx").write_text("x", encoding="utf-8")
            (new_dir / "simple_score_report.xlsx").write_text("x", encoding="utf-8")
            req = ExportRequest(output_dir=new_dir)
            meta = {"exam_name": "demo", "class_name": "Test",
                    "subject": "Math", "exam_date": "2026-07-09"}
            ReportIndexHtmlExporter().export(
                req, meta,
                new_dir / "simple_report.html",
                new_dir / "advanced_dashboard.html",
                new_dir / "simple_score_report.xlsx")

            return leg_dir / "index.html", new_dir / "index.html", t
        except Exception:
            shutil.rmtree(t, ignore_errors=True)
            raise

    def test_file_exists(self):
        leg, new, t = self._generate_both()
        try:
            self.assertTrue(leg.exists())
            self.assertTrue(new.exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_has_html_tags(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("<html", html)
                self.assertIn("</html>", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_title_matches(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("批改完成", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_links_to_simple_report(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("simple_report.html", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_links_to_advanced_dashboard(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("advanced_dashboard.html", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_links_to_simple_score_xlsx(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("simple_score_report.xlsx", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_chinese_not_garbled(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("批改完成", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src_path = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
                    / "report_index_html_exporter.py")
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)

    def test_no_web_import(self):
        src_path = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
                    / "report_index_html_exporter.py")
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("web", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("web", node.module)


if __name__ == "__main__":
    unittest.main()
