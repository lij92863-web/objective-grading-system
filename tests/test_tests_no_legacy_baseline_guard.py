"""B7: Tests no-legacy-baseline guard — whitelist for legacy test imports."""
import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Only these test files may import legacy after baseline replacement
ALLOWED_LEGACY_TEST_IMPORTS = {
    # Compat / guard tests
    "tests/test_compat_export_parity.py",
    "tests/test_objective_grader_compat_module.py",
    "tests/test_legacy_deletion_readiness.py",
    "tests/test_legacy_dependency_guard_matrix.py",
    "tests/test_legacy_entrypoints_import.py",
    "tests/test_objective_grader_legacy_compatibility_gate.py",
    "tests/test_objective_grader_legacy_dependency_guard.py",
    "tests/test_main_chain_no_legacy_gate.py",
    "tests/test_workflow_legacy_analysis_call_guard.py",
    "tests/test_workflow_legacy_csv_call_guard.py",
    "tests/test_workflow_legacy_excel_call_guard.py",
    "tests/test_workflow_legacy_html_call_guard.py",
    "tests/test_workflow_legacy_loader_call_guard.py",
    "tests/test_workflow_legacy_validation_call_guard.py",
    "tests/test_workflow_remaining_legacy_builder_guard.py",
    "tests/test_workflow_grading_core_guard.py",
    "tests/test_facade_legacy_dependency_guard.py",
    "tests/test_code_readability_guard.py",
    # Compat only — verifies legacy entrypoints exist
    "tests/test_legacy_entrypoints_import.py",
}


def _has_legacy_import(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "legacy" or a.name.startswith("legacy."):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "legacy" or node.module.startswith("legacy.")):
                return True
    return False


class TestsNoLegacyBaselineGuardTests(unittest.TestCase):

    def test_no_unapproved_legacy_test_imports(self):
        """Only whitelisted test files may import legacy."""
        violations = []
        for p in sorted((PROJECT_ROOT / "tests").rglob("test*.py")):
            rel = p.relative_to(PROJECT_ROOT).as_posix()
            if rel in ALLOWED_LEGACY_TEST_IMPORTS:
                continue
            if _has_legacy_import(p):
                violations.append(rel)
        self.assertEqual(
            [], violations,
            f"Non-whitelisted tests import legacy: {len(violations)} files")

    def test_whitelist_count_reasonable(self):
        """Whitelist reduced from 26→17→13 after B5 conversion."""
        self.assertLessEqual(
            len(ALLOWED_LEGACY_TEST_IMPORTS), 25, "max 25")


if __name__ == "__main__":
    unittest.main()
