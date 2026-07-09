"""Tests for AdvancedDashboardHtmlExporter — E4D."""

import ast
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from app.infrastructure.exporters.advanced_dashboard_html_exporter import (
    AdvancedDashboardHtmlExporter,
)
from app.infrastructure.exporters.contracts import ExportRequest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class AdvancedDashboardHtmlExporterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _generate_both(self):
        t = tempfile.mkdtemp(prefix="e4d_", dir=PROJECT_ROOT / "data")
        try:
            import legacy.objective_grader_legacy as leg
            ak = leg.load_answer_key(DEMO_KEY)
            subs = leg.load_submissions(DEMO_SUB, ak)
            results = leg.grade_all(ak, subs)
            profiles = leg.build_knowledge_profiles(ak, results)
            item_rows = leg.item_stats(ak, results)
            validation_rows = leg.build_validation_report(
                ak, subs, results, profiles)
            meta_obj = leg.ExamMeta(exam_name="demo", class_name="Test",
                                    subject="Math", exam_date="2026-07-09")

            # Legacy
            leg_dir = Path(t) / "legacy"
            leg_dir.mkdir()
            leg.write_advanced_dashboard(
                leg_dir / "advanced_dashboard.html", meta_obj,
                results, profiles, validation_rows, item_rows)

            # New
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            meta = {"exam_name": "demo", "class_name": "Test",
                    "subject": "Math", "exam_date": "2026-07-09"}
            AdvancedDashboardHtmlExporter().export(
                req, meta, results, profiles, validation_rows, item_rows)

            return (leg_dir / "advanced_dashboard.html",
                    new_dir / "advanced_dashboard.html", t)
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

    def test_file_size_reasonable(self):
        leg, new, t = self._generate_both()
        try:
            self.assertGreater(leg.stat().st_size, 500)
            self.assertGreater(new.stat().st_size, 500)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_title_matches(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("高级学情分析报告", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_key_sections_present(self):
        leg, new, t = self._generate_both()
        try:
            sections = ["成绩分布", "每题正确率", "易错题",
                        "班级薄弱知识点", "答题异常", "教学讲评建议",
                        "每题选项分布"]
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                for sec in sections:
                    self.assertIn(sec, html,
                                  f"'{sec}' missing from {fp.name}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_has_css(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("<style>", html)
                self.assertIn("--bg:", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_metric_cards_present(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                for label in ["参考人数", "平均分", "最高分", "最低分",
                              "及格率", "优秀率"]:
                    self.assertIn(label, html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_chinese_not_garbled(self):
        leg, new, t = self._generate_both()
        try:
            for fp in [leg, new]:
                html = fp.read_text(encoding="utf-8")
                self.assertIn("高级学情分析报告", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src_path = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
                    / "advanced_dashboard_html_exporter.py")
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
                    / "advanced_dashboard_html_exporter.py")
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("web", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("web", node.module)

    def test_old_workflow_still_unaffected(self):
        t = tempfile.mkdtemp(prefix="e4d_wf_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                            no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
            self.assertTrue(
                (Path(t) / "advanced_dashboard.html").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
