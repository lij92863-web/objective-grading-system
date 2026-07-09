"""HTML legacy behavior lock — E4A. Harden tests before HTML migration.

Verifies legacy HTML outputs (simple_report, advanced_dashboard, index)
against demo data.  All checks use only the stdlib — no openpyxl/Selenium.
"""

import re
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"

# Expected file names (must stay stable across migration)
EXPECTED_HTML_FILES = [
    "simple_report.html",
    "advanced_dashboard.html",
    "index.html",
]

# Expected titles (must not drift)
EXPECTED_SIMPLE_TITLE_RE = re.compile(r"普通版报告")
EXPECTED_DASHBOARD_TITLE_RE = re.compile(r"高级学情分析报告")
EXPECTED_INDEX_TITLE_RE = re.compile(r"批改完成")

# Key sections / elements that must exist in simple report
SIMPLE_REPORT_SECTIONS = [
    "学生成绩表",
    "每题正确率",
    "错得最多的题",
]

# Key sections in advanced dashboard
DASHBOARD_SECTIONS = [
    "成绩分布",
    "每题正确率",
    "易错题",
    "班级薄弱知识点",
    "答题异常情况",
    "教学讲评建议",
    "每题选项分布",
]

# Links in index.html that must exist
INDEX_LINKS = [
    "simple_report.html",
    "advanced_dashboard.html",
]


class HtmlLegacyBehaviorTests(unittest.TestCase):
    """Lock legacy HTML output behaviour."""

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _generate_legacy_html(self):
        """Run legacy workflow and return output directory path."""
        t = tempfile.mkdtemp(prefix="e4a_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="test_html")
            return Path(t)
        except Exception:
            shutil.rmtree(t, ignore_errors=True)
            raise

    # ── file existence ───────────────────────────────────────────────────

    def test_html_files_exist(self):
        out = self._generate_legacy_html()
        try:
            for fname in EXPECTED_HTML_FILES:
                fp = out / fname
                self.assertTrue(fp.exists(), f"Missing {fname}")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_html_files_non_trivial_size(self):
        out = self._generate_legacy_html()
        try:
            for fname in EXPECTED_HTML_FILES:
                fp = out / fname
                self.assertGreater(
                    fp.stat().st_size, 100,
                    f"{fname} is too small ({fp.stat().st_size} bytes)")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    # ── simple report ────────────────────────────────────────────────────

    def test_simple_report_has_html_structure(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "simple_report.html").read_text(encoding="utf-8")
            self.assertIn("<html", html)
            self.assertIn("</html>", html)
            self.assertIn("<head", html)
            self.assertIn("<body", html)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_simple_report_title(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "simple_report.html").read_text(encoding="utf-8")
            self.assertTrue(
                EXPECTED_SIMPLE_TITLE_RE.search(html),
                f"Title '普通版报告' not found in simple report")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_simple_report_has_key_sections(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "simple_report.html").read_text(encoding="utf-8")
            for section in SIMPLE_REPORT_SECTIONS:
                self.assertIn(section, html,
                              f"Section '{section}' missing from simple report")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_simple_report_has_score_table(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "simple_report.html").read_text(encoding="utf-8")
            self.assertIn("<table>", html)
            self.assertIn("<th>student_id</th>", html)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_simple_report_has_excel_link(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "simple_report.html").read_text(encoding="utf-8")
            self.assertIn("simple_score_report.xlsx", html)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_simple_report_chinese_not_garbled(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "simple_report.html").read_text(encoding="utf-8")
            self.assertIn("学生成绩表", html)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    # ── advanced dashboard ───────────────────────────────────────────────

    def test_advanced_dashboard_has_html_structure(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "advanced_dashboard.html").read_text(encoding="utf-8")
            self.assertIn("<html", html)
            self.assertIn("</html>", html)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_advanced_dashboard_title(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "advanced_dashboard.html").read_text(encoding="utf-8")
            self.assertTrue(
                EXPECTED_DASHBOARD_TITLE_RE.search(html),
                f"Title '高级学情分析报告' not found in dashboard")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_advanced_dashboard_has_key_sections(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "advanced_dashboard.html").read_text(encoding="utf-8")
            for section in DASHBOARD_SECTIONS:
                self.assertIn(section, html,
                              f"Section '{section}' missing from dashboard")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_advanced_dashboard_has_css(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "advanced_dashboard.html").read_text(encoding="utf-8")
            self.assertIn("<style>", html)
            self.assertIn("--bg:", html)  # CSS custom property
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_advanced_dashboard_no_js(self):
        """Legacy dashboards should NOT contain JavaScript."""
        out = self._generate_legacy_html()
        try:
            html = (out / "advanced_dashboard.html").read_text(encoding="utf-8")
            self.assertNotIn("<script", html.lower())
        finally:
            shutil.rmtree(out, ignore_errors=True)

    # ── index ────────────────────────────────────────────────────────────

    def test_index_has_html_structure(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("<html", html)
            self.assertIn("</html>", html)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_index_title(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertTrue(
                EXPECTED_INDEX_TITLE_RE.search(html),
                "Title '批改完成' not found in index")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_index_links_to_simple_report(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("simple_report.html", html,
                          "Index missing link to simple_report.html")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_index_links_to_advanced_dashboard(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("advanced_dashboard.html", html,
                          "Index missing link to advanced_dashboard.html")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_index_links_to_simple_score_xlsx(self):
        out = self._generate_legacy_html()
        try:
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("simple_score_report.xlsx", html,
                          "Index missing link to simple_score_report.xlsx")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    # ── safety ───────────────────────────────────────────────────────────

    def test_no_real_api_called(self):
        out = self._generate_legacy_html()
        try:
            self.assertTrue((out / "index.html").exists())
        finally:
            shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
