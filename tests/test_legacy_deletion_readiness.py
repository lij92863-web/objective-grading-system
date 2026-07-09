"""Legacy deletion readiness scan — L16A. Read-only, does NOT delete anything."""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _rglob_py(root: str):
    return sorted((PROJECT_ROOT / root).rglob("*.py"))


def _imports_legacy(path: Path) -> list:
    """Return [module_name] for any legacy import in the file."""
    result = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "legacy" in alias.name:
                    result.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and "legacy" in node.module:
                result.append(node.module)
    return result


class LegacyDeletionReadinessTests(unittest.TestCase):
    """Read-only: scan what still imports legacy."""

    def test_domain_does_not_import_legacy(self):
        for f in _rglob_py("app/domain"):
            imps = _imports_legacy(f)
            self.assertEqual([], imps, f"{f} imports legacy: {imps}")

    def test_application_does_not_import_legacy(self):
        for f in _rglob_py("app/application"):
            imps = _imports_legacy(f)
            self.assertEqual([], imps, f"{f} imports legacy: {imps}")

    def test_infrastructure_does_not_import_legacy(self):
        for f in _rglob_py("app/infrastructure"):
            imps = _imports_legacy(f)
            self.assertEqual([], imps, f"{f} imports legacy: {imps}")

    def test_shared_does_not_import_legacy(self):
        sp = PROJECT_ROOT / "app" / "shared"
        if sp.exists():
            for f in _rglob_py("app/shared"):
                imps = _imports_legacy(f)
                self.assertEqual([], imps, f"{f} imports legacy: {imps}")

    def test_workflow_imports_legacy_recorded(self):
        """workflow.py imports legacy — recorded as known state."""
        imps = _imports_legacy(PROJECT_ROOT / "app" / "workflow.py")
        self.assertTrue(imps, "workflow.py should still import legacy")

    def test_objective_grader_imports_legacy_recorded(self):
        imps = _imports_legacy(PROJECT_ROOT / "objective_grader.py")
        self.assertTrue(imps, "objective_grader.py should still import legacy")

    def test_tests_import_legacy_allowed(self):
        """Tests can import legacy for baseline comparisons."""
        count = sum(1 for f in _rglob_py("tests") if _imports_legacy(f))
        self.assertGreater(count, 0, "Tests should still reference legacy")


if __name__ == "__main__":
    unittest.main()
