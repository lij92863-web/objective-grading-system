"""Baseline fixture integrity — B3."""
import ast
import json
import unittest
from pathlib import Path
from tests.helpers.baseline_fixtures import (
    FIXTURES_ROOT, load_json_fixture, load_csv_fixture,
    normalize_xlsx_structure, normalize_html_structure,
)


class BaselineFixtureIntegrityTests(unittest.TestCase):
    def test_directories_exist(self):
        for d in ["json", "csv", "html_structures", "xlsx_structures"]:
            self.assertTrue((FIXTURES_ROOT / d).is_dir(),
                            f"Missing fixture dir: {d}")

    def test_json_fixtures_parseable(self):
        for f in (FIXTURES_ROOT / "json").glob("*.json"):
            with self.subTest(file=f.name):
                data = json.loads(f.read_text("utf-8"))
                self.assertIsInstance(data, (dict, list))
                self.assertGreater(len(data), 0, f"{f.name} is empty")

    def test_csv_fixtures_parseable(self):
        for f in (FIXTURES_ROOT / "csv").glob("*.csv"):
            with self.subTest(file=f.name):
                rows = load_csv_fixture(f.stem)
                self.assertIsInstance(rows, list)

    def test_html_structure_fixtures_parseable(self):
        for f in (FIXTURES_ROOT / "html_structures").glob("*.json"):
            with self.subTest(file=f.name):
                data = json.loads(f.read_text("utf-8"))
                self.assertIn("title", data)
                self.assertIn("sections", data)
                self.assertIn("links", data)

    def test_xlsx_structure_fixtures_parseable(self):
        for f in (FIXTURES_ROOT / "xlsx_structures").glob("*.json"):
            with self.subTest(file=f.name):
                data = json.loads(f.read_text("utf-8"))
                self.assertIn("sheet_names", data)
                self.assertIn("headers", data)

    def test_helper_no_legacy_import(self):
        src = (Path(__file__).parents[1] / "tests" / "helpers"
               / "baseline_fixtures.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)


if __name__ == "__main__":
    unittest.main()
