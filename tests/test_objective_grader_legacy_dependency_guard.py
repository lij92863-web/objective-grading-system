import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_LEGACY_CALLS = {"create_sample_files"}
FORBIDDEN_COMPAT_CALLS = {
    "load_answer_key",
    "load_submissions",
    "grade_all",
    "build_knowledge_profiles",
    "build_validation_report",
    "basic_stats",
    "write_summary",
    "write_detail",
    "write_item_analysis",
    "write_knowledge_profiles",
    "write_practice_recommendations",
    "write_class_report",
    "write_validation_report",
    "write_student_report",
    "write_workbook",
    "write_simple_score_workbook",
    "write_simple_report",
    "write_advanced_dashboard",
    "write_report_index",
}


class ObjectiveGraderLegacyDependencyGuardTests(unittest.TestCase):
    def setUp(self):
        self.source_path = PROJECT_ROOT / "objective_grader.py"
        self.tree = ast.parse(self.source_path.read_text(encoding="utf-8"))

    def test_no_star_import_from_legacy(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom) and node.module == "legacy.objective_grader_legacy":
                self.assertFalse(
                    any(alias.name == "*" for alias in node.names),
                    "objective_grader.py must use an explicit compatibility whitelist",
                )

    def test_direct_legacy_calls_are_whitelisted(self):
        direct_calls = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "legacy"
            ):
                direct_calls.append(func.attr)

        self.assertTrue(set(direct_calls) <= ALLOWED_LEGACY_CALLS, direct_calls)
        self.assertFalse(set(direct_calls) & FORBIDDEN_COMPAT_CALLS)

    def test_compat_exports_are_explicit(self):
        text = self.source_path.read_text(encoding="utf-8")
        self.assertIn("COMPAT_EXPORTS", text)
        self.assertIn("globals().update", text)


if __name__ == "__main__":
    unittest.main()
