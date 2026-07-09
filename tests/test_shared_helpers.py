"""Tests for app/shared helpers — L13B/C."""

import ast
import unittest
from pathlib import Path

from app.shared.string_helpers import (
    display_percent,
    main_wrong_answer_from_distribution,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SharedHelpersTests(unittest.TestCase):
    def test_display_percent_valid(self):
        self.assertEqual(display_percent(95.5), "95.50%")

    def test_display_percent_invalid(self):
        self.assertEqual(display_percent("abc"), "0.00%")

    def test_display_percent_zero(self):
        self.assertEqual(display_percent(0), "0.00%")

    def test_main_wrong_answer_returns_max(self):
        dist = {"A": 5, "B": 10, "C": 2}
        result = main_wrong_answer_from_distribution(dist, "D")
        self.assertIn("B", result)

    def test_main_wrong_answer_blank_excluded(self):
        dist = {"(blank)": 5, "B": 3}
        result = main_wrong_answer_from_distribution(dist, "")
        self.assertIn("B", result)

    def test_main_wrong_answer_empty(self):
        self.assertEqual(main_wrong_answer_from_distribution({}), "")

    def test_no_legacy_import(self):
        src = (PROJECT_ROOT / "app" / "shared"
               / "string_helpers.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)

    def test_no_web_import(self):
        src = (PROJECT_ROOT / "app" / "shared"
               / "string_helpers.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("web", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("web", node.module)


if __name__ == "__main__":
    unittest.main()
