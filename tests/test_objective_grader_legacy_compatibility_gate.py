"""Objective grader compatibility gate — D5."""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# objective_grader.py MUST NOT directly call these legacy functions
# in ordinary CLI path (--make-samples and demo creation excluded)
FORBIDDEN_DIRECT_CALLS = {
    "grade_all", "load_answer_key", "load_submissions",
    "write_summary", "write_detail", "write_item_analysis",
    "write_workbook", "write_simple_score_workbook",
    "write_simple_report", "write_advanced_dashboard", "write_report_index",
    "create_sample_files",  # now migrated
}


class ObjectiveGraderCompatibilityGateTests(unittest.TestCase):

    def test_no_star_import(self):
        src = (PROJECT_ROOT / "objective_grader.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "legacy.objective_grader_legacy":
                    self.assertFalse(
                        any(a.name == "*" for a in node.names),
                        "Star import from legacy is forbidden")

    def test_compat_exports_is_explicit_tuple(self):
        src = (PROJECT_ROOT / "objective_grader.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Name)
                            and target.id == "COMPAT_EXPORTS"):
                        self.assertIsInstance(node.value, ast.Tuple,
                                              "COMPAT_EXPORTS must be a tuple")

    def test_compat_exports_no_duplicates(self):
        src = (PROJECT_ROOT / "objective_grader.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Name)
                            and target.id == "COMPAT_EXPORTS"):
                        names = [e.value for e in node.value.elts
                                 if isinstance(e, ast.Constant)]
                        self.assertEqual(len(names), len(set(names)),
                                         "COMPAT_EXPORTS has duplicates")

    def test_ordinary_path_no_legacy_grading_calls(self):
        """Ordinary CLI path must not call legacy grading/report/loader."""
        src = (PROJECT_ROOT / "objective_grader.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "legacy"):
                    self.assertNotIn(
                        func.attr, FORBIDDEN_DIRECT_CALLS,
                        f"objective_grader must not call legacy.{func.attr}")


if __name__ == "__main__":
    unittest.main()
