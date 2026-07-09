"""Tests for html_helpers — E4B."""

import ast
import unittest
from pathlib import Path

from app.infrastructure.exporters import html_helpers as H

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class HtmlEscapeTests(unittest.TestCase):
    def test_angle_brackets(self):
        self.assertEqual(H.html_escape("<a>"), "&lt;a&gt;")

    def test_ampersand(self):
        self.assertEqual(H.html_escape("A & B"), "A &amp; B")

    def test_double_quote(self):
        self.assertIn("&quot;", H.html_escape('"'))

    def test_single_quote(self):
        self.assertIn("&#x27;", H.html_escape("'"))

    def test_chinese_preserved(self):
        self.assertEqual(H.html_escape("普通版报告"), "普通版报告")

    def test_none_handling(self):
        self.assertEqual(H.html_escape(None), "None")

    def test_empty_string(self):
        self.assertEqual(H.html_escape(""), "")


class FormattingTests(unittest.TestCase):
    def test_pct(self):
        self.assertEqual(H.pct(95), "95.00%")

    def test_percent_valid(self):
        self.assertEqual(H.percent(80.5), "80.50%")

    def test_percent_invalid(self):
        self.assertEqual(H.percent("abc"), "0.00%")

    def test_get_rate_class_danger(self):
        self.assertEqual(H.get_rate_class(30), "danger")

    def test_get_rate_class_warning(self):
        self.assertEqual(H.get_rate_class(50), "warning")

    def test_get_rate_class_normal(self):
        self.assertEqual(H.get_rate_class(70), "normal")

    def test_get_rate_class_good(self):
        self.assertEqual(H.get_rate_class(90), "good")


class SafeSlugTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(H.safe_slug("Hello World"), "hello_world")

    def test_chinese(self):
        slug = H.safe_slug("测试")
        self.assertIn("测试", slug)

    def test_none(self):
        self.assertEqual(H.safe_slug(None), "exam")


class RenderTableTests(unittest.TestCase):
    def test_basic_table(self):
        html = H.render_table(["A", "B"], [["1", "2"]])
        self.assertIn("<th>A</th>", html)
        self.assertIn("<td>1</td>", html)
        self.assertIn("<table>", html)

    def test_escape_in_table(self):
        html = H.render_table(["<X>"], [["&"]])
        self.assertIn("&lt;X&gt;", html)
        self.assertIn("&amp;", html)


class BarTests(unittest.TestCase):
    def test_bar_html(self):
        html = H.bar("Q1", 75.5)
        self.assertIn("75.5", html)
        self.assertIn("Q1", html)


class ReportLinkTests(unittest.TestCase):
    def test_link_output(self):
        import tempfile, shutil
        t = tempfile.mkdtemp(prefix="e4b_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "test.html"
            fp.write_text("x", encoding="utf-8")
            html = H.report_link(fp, "查看", "btn-primary")
            self.assertIn("test.html", html)
            self.assertIn("查看", html)
        finally:
            shutil.rmtree(t, ignore_errors=True)


class CssTests(unittest.TestCase):
    def test_report_css_non_empty(self):
        css = H.report_css()
        self.assertIn("body{", css)

    def test_advanced_dashboard_css_non_empty(self):
        css = H.advanced_dashboard_css()
        self.assertIn(":root{", css)

    def test_index_css_non_empty(self):
        css = H.index_css()
        self.assertIn("body{", css)


class GuardTests(unittest.TestCase):
    def test_no_legacy_import(self):
        src = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
               / "html_helpers.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)

    def test_no_web_import(self):
        src = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
               / "html_helpers.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("web", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("web", node.module)

    def test_writing_utf8(self):
        """Verify the module is valid utf-8."""
        (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
         / "html_helpers.py").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
