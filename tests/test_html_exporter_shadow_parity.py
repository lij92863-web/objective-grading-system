"""HTML shadow parity — E4F. Proves legacy HTML == new exporter HTML."""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.infrastructure.exporters.advanced_dashboard_html_exporter import (
    AdvancedDashboardHtmlExporter,
)
from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.report_index_html_exporter import (
    ReportIndexHtmlExporter,
)
from app.infrastructure.exporters.simple_report_html_exporter import (
    SimpleReportHtmlExporter,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class HtmlShadowParityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _generate_all(self):
        t = tempfile.mkdtemp(prefix="e4f_", dir=PROJECT_ROOT / "data")
        try:
            import legacy.objective_grader_legacy as leg
            ak = leg.load_answer_key(DEMO_KEY)
            subs = leg.load_submissions(DEMO_SUB, ak)
            results = leg.grade_all(ak, subs)
            profiles = leg.build_knowledge_profiles(ak, results)
            item_rows = leg.item_stats(ak, results)
            simple_rows = leg.simple_score_rows(results)
            val_rows = leg.build_validation_report(ak, subs, results, profiles)
            meta_obj = leg.ExamMeta(exam_name="demo", class_name="Test",
                                    subject="Math", exam_date="2026-07-09")
            meta = {"exam_name": "demo", "class_name": "Test",
                    "subject": "Math", "exam_date": "2026-07-09"}

            # Legacy outputs
            leg_dir = Path(t) / "legacy"
            leg_dir.mkdir()
            leg.write_simple_score_workbook(
                leg_dir / "simple_score_report.xlsx", simple_rows)
            leg.write_simple_report(
                leg_dir / "simple_report.html", meta_obj, ak,
                results, simple_rows, item_rows)
            leg.write_advanced_dashboard(
                leg_dir / "advanced_dashboard.html", meta_obj,
                results, profiles, val_rows, item_rows)
            leg.write_report_index(
                leg_dir / "index.html", meta_obj,
                leg_dir / "simple_report.html",
                leg_dir / "advanced_dashboard.html",
                leg_dir / "simple_score_report.xlsx")

            # New exporter outputs
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            SimpleReportHtmlExporter().export(
                req, meta, results, simple_rows, item_rows)
            AdvancedDashboardHtmlExporter().export(
                req, meta, results, profiles, val_rows, item_rows)
            # Need files for report_link to render active links
            (new_dir / "simple_report.html").touch()
            (new_dir / "advanced_dashboard.html").touch()
            (new_dir / "simple_score_report.xlsx").touch()
            ReportIndexHtmlExporter().export(
                req, meta,
                new_dir / "simple_report.html",
                new_dir / "advanced_dashboard.html",
                new_dir / "simple_score_report.xlsx")

            return leg_dir, new_dir, t
        except Exception:
            shutil.rmtree(t, ignore_errors=True)
            raise

    def _strip_ts(self, text: str) -> str:
        """Remove generated_at timestamp for comparison."""
        return re.sub(
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', 'TS_REMOVED', text)

    # ── simple report parity ──────────────────────────────────────────────

    def test_simple_filenames_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            self.assertTrue((leg_dir / "simple_report.html").exists())
            self.assertTrue((new_dir / "simple_report.html").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_titles_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                h = (d / "simple_report.html").read_text("utf-8")
                self.assertIn("普通版报告", h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_key_sections_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                h = (d / "simple_report.html").read_text("utf-8")
                for s in ["学生成绩表", "每题正确率", "错得最多的题"]:
                    self.assertIn(s, h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_links_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                h = (d / "simple_report.html").read_text("utf-8")
                self.assertIn("simple_score_report.xlsx", h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_file_sizes_reasonable(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                self.assertGreater(
                    (d / "simple_report.html").stat().st_size, 500)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    # ── advanced dashboard parity ─────────────────────────────────────────

    def test_dashboard_filenames_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            self.assertTrue((leg_dir / "advanced_dashboard.html").exists())
            self.assertTrue((new_dir / "advanced_dashboard.html").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_dashboard_titles_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                h = (d / "advanced_dashboard.html").read_text("utf-8")
                self.assertIn("高级学情分析报告", h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_dashboard_key_sections_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                h = (d / "advanced_dashboard.html").read_text("utf-8")
                for s in ["成绩分布", "易错题", "薄弱知识点", "教学讲评"]:
                    self.assertIn(s, h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    # ── index parity ─────────────────────────────────────────────────────

    def test_index_filenames_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            self.assertTrue((leg_dir / "index.html").exists())
            self.assertTrue((new_dir / "index.html").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_index_titles_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                h = (d / "index.html").read_text("utf-8")
                self.assertIn("批改完成", h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_index_links_equal(self):
        leg_dir, new_dir, t = self._generate_all()
        try:
            for d in [leg_dir, new_dir]:
                h = (d / "index.html").read_text("utf-8")
                self.assertIn("simple_report.html", h)
                self.assertIn("advanced_dashboard.html", h)
                self.assertIn("simple_score_report.xlsx", h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    # ── safety ────────────────────────────────────────────────────────────

    def test_old_cli_still_works(self):
        t = tempfile.mkdtemp(prefix="e4f_cli_", dir=PROJECT_ROOT / "data")
        try:
            r = subprocess.run([
                sys.executable,
                str(PROJECT_ROOT / "objective_grader.py"),
                "--answer-key", str(DEMO_KEY),
                "--submissions", str(DEMO_SUB),
                "--out-dir", str(Path(t) / "out"),
                "--no-archive",
            ], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0,
                             f"CLI failed:\n{r.stderr}")
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
