"""Tests for SimpleReportHtmlExporter — E4C."""

import ast
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.simple_report_html_exporter import (
    SimpleReportHtmlExporter,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class SimpleReportHtmlExporterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _generate_both(self):
        """Return (legacy_html_path, new_html_path, tmpdir)."""
        t = tempfile.mkdtemp(prefix="e4c_", dir=PROJECT_ROOT / "data")
        try:
            # Legacy
            import legacy.objective_grader_legacy as leg
            ak = leg.load_answer_key(DEMO_KEY)
            subs = leg.load_submissions(DEMO_SUB, ak)
            results = leg.grade_all(ak, subs)
            simple_rows = leg.simple_score_rows(results)
            item_rows = leg.item_stats(ak, results)
            meta_obj = leg.ExamMeta(exam_name="demo", class_name="Test",
                                    subject="Math", exam_date="2026-07-09")

            leg_dir = Path(t) / "legacy"
            leg_dir.mkdir()
            leg.write_simple_report(
                leg_dir / "simple_report.html", meta_obj, ak,
                results, simple_rows, item_rows)

            # New exporter
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            meta_dict = {"exam_name": "demo", "class_name": "Test",
                          "subject": "Math", "exam_date": "2026-07-09"}
            SimpleReportHtmlExporter().export(
                req, meta_dict, results, simple_rows, item_rows)

            return (leg_dir / "simple_report.html",
                    new_dir / "simple_report.html", t)
        except Exception:
            shutil.rmtree(t, ignore_errors=True)
            raise

    def _norm(self, text: str) -> str:
        """Normalize whitespace for comparison."""
        return re.sub(r'\s+', ' ', text).strip()

    def test_file_exists(self):
        leg, new, t = self._generate_both()
        try:
            self.assertTrue(leg.exists())
            self.assertTrue(new.exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_file_size_reasonable(self):
        leg, new, t = self._generate_both()
        try:
            self.assertGreater(leg.stat().st_size, 500)
            self.assertGreater(new.stat().st_size, 500)
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
                self.assertIn("普通版报告", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_key_sections_present(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                for sec in ["学生成绩表", "每题正确率", "错得最多的题"]:
                    self.assertIn(sec, html,
                                  f"'{sec}' missing from {fp.name}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_headers_match(self):
        leg, new, t = self._generate_both()
        try:
            leg_html = leg.read_text(encoding="utf-8")
            new_html = new.read_text(encoding="utf-8")
            # Both should contain the same <th> elements
            leg_ths = set(re.findall(r'<th>(.*?)</th>', leg_html))
            new_ths = set(re.findall(r'<th>(.*?)</th>', new_html))
            self.assertEqual(leg_ths, new_ths,
                             f"TH mismatch:\nlegacy={leg_ths}\nnew={new_ths}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_excel_link_present(self):
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
                self.assertIn("学生成绩表", html)
                self.assertIn("普通版报告", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src_path = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "simple_report_html_exporter.py"
        )
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)

    def test_no_web_import(self):
        src_path = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "simple_report_html_exporter.py"
        )
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("web", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("web", node.module)

    def test_old_workflow_still_unaffected(self):
        t = tempfile.mkdtemp(prefix="e4c_wf_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                            no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
            self.assertTrue((Path(t) / "simple_report.html").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
