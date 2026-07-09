"""Readability guard coverage for HTML helper exceptions.

The global guard may allow long lines only in explicit CSS template helpers.
It must not skip all of html_helpers.py or the HTML exporter package.
"""

import unittest
from pathlib import Path

from tests import test_code_readability_guard as guard


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTML_HELPERS = (
    PROJECT_ROOT / "app" / "infrastructure" / "exporters" / "html_helpers.py"
)
EXPORTER_NAMES = {
    "simple_report_html_exporter.py",
    "advanced_dashboard_html_exporter.py",
    "report_index_html_exporter.py",
}


class HtmlHelpersReadabilityGuardTests(unittest.TestCase):
    def test_html_helpers_not_whole_file_whitelisted(self):
        self.assertNotIn("html_helpers.py", guard.LONG_LINE_WHITELIST)

    def test_html_exporters_not_whole_file_whitelisted(self):
        self.assertTrue(
            EXPORTER_NAMES.isdisjoint(guard.LONG_LINE_WHITELIST),
            f"HTML exporters are whole-file whitelisted: "
            f"{EXPORTER_NAMES & guard.LONG_LINE_WHITELIST}",
        )

    def test_only_named_css_template_functions_allow_long_lines(self):
        ranges = guard._function_line_ranges(HTML_HELPERS)
        for function_name in guard.HTML_HELPER_ALLOWED_LONG_LINE_FUNCTIONS:
            self.assertIn(function_name, ranges)

        disallowed_long_lines = []
        for lineno, line in enumerate(
            HTML_HELPERS.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if len(line) <= guard.MAX_LINE_LENGTH:
                continue
            if not guard._is_allowed_long_line(HTML_HELPERS, lineno):
                disallowed_long_lines.append(lineno)

        self.assertEqual([], disallowed_long_lines)

    def test_regular_logic_line_would_not_be_allowed(self):
        ranges = guard._function_line_ranges(HTML_HELPERS)
        html_escape_line = ranges["html_escape"].start

        self.assertFalse(
            guard._is_allowed_long_line(HTML_HELPERS, html_escape_line)
        )


if __name__ == "__main__":
    unittest.main()
