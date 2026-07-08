"""Architecture boundary tests — Stage 1.

Locks module dependency rules with AST-based import scanning.
Prevents future accidental coupling across architectural layers.
"""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _py_files(root: str) -> list[Path]:
    return sorted(Path(PROJECT_ROOT, root).rglob("*.py"))


def _imports(filepath: Path) -> list[str]:
    """Return every imported module name from *filepath*."""
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                names.append(f"{mod}.{alias.name}" if mod else alias.name)
    return names


def _any_name_starts(namelist: list[str], prefixes: tuple[str, ...]) -> list[str]:
    return [n for n in namelist if n.startswith(prefixes)]


# ---------------------------------------------------------------------------
# forbidden prefix groups
# ---------------------------------------------------------------------------

FORBIDDEN_LEGACY = ("legacy",)
FORBIDDEN_WEB = (
    "web_app",
    "objective_grader",
    "web",
    "app.infrastructure",
    "app.application",
)

# ---------------------------------------------------------------------------
# 1. Domain layer
# ---------------------------------------------------------------------------


class DomainLayerBoundaryTests(unittest.TestCase):
    """app/domain must not depend on legacy, web, recognition, or I/O."""

    def test_domain_does_not_import_legacy(self):
        for f in _py_files("app/domain"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), FORBIDDEN_LEGACY)
                self.assertEqual([], hits, f"{f} imports legacy: {hits}")

    def test_domain_does_not_import_web_or_cli(self):
        for f in _py_files("app/domain"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), FORBIDDEN_WEB)
                self.assertEqual([], hits, f"{f} imports web/cli: {hits}")

    def test_domain_does_not_import_recognition(self):
        for f in _py_files("app/domain"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), ("app.recognition",))
                self.assertEqual(
                    [], hits, f"{f} imports recognition: {hits}"
                )


# ---------------------------------------------------------------------------
# 2. Recognition layer
# ---------------------------------------------------------------------------


class RecognitionLayerBoundaryTests(unittest.TestCase):
    """app/recognition must not depend on legacy or web layers."""

    def test_recognition_does_not_import_legacy(self):
        for f in _py_files("app/recognition"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), FORBIDDEN_LEGACY)
                self.assertEqual(
                    [], hits, f"{f} imports legacy: {hits}"
                )

    def test_recognition_does_not_import_web_or_cli(self):
        for f in _py_files("app/recognition"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), FORBIDDEN_WEB)
                self.assertEqual(
                    [], hits, f"{f} imports web/cli: {hits}"
                )


# ---------------------------------------------------------------------------
# 3. Qwen adapter layer
# ---------------------------------------------------------------------------


class QwenAdapterBoundaryTests(unittest.TestCase):
    """qwen_adapter must not depend on legacy or UI."""

    def test_qwen_adapter_does_not_import_legacy(self):
        for f in _py_files("app/recognition/qwen_adapter"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), FORBIDDEN_LEGACY)
                self.assertEqual(
                    [], hits, f"{f} imports legacy: {hits}"
                )

    def test_qwen_adapter_does_not_import_web(self):
        for f in _py_files("app/recognition/qwen_adapter"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), ("web_app", "web",))
                self.assertEqual(
                    [], hits, f"{f} imports web: {hits}"
                )


# ---------------------------------------------------------------------------
# 4. Legacy must not import new modules
# ---------------------------------------------------------------------------


class LegacyFreezeBoundaryTests(unittest.TestCase):
    """Legacy must not import new architecture modules."""

    def test_legacy_does_not_import_recognition(self):
        for f in _py_files("legacy"):
            with self.subTest(file=str(f)):
                imps = _imports(f)
                hits = _any_name_starts(imps, ("app.recognition",))
                self.assertEqual(
                    [], hits, f"{f} imports recognition: {hits}"
                )

    def test_legacy_does_not_import_qwen_adapter(self):
        for f in _py_files("legacy"):
            with self.subTest(file=str(f)):
                imps = _imports(f)
                hits = _any_name_starts(
                    imps, ("app.recognition.qwen_adapter",)
                )
                self.assertEqual(
                    [], hits, f"{f} imports qwen_adapter: {hits}"
                )


# ---------------------------------------------------------------------------
# 5. Application layer
# ---------------------------------------------------------------------------


class ApplicationLayerBoundaryTests(unittest.TestCase):
    """app/application must not depend on legacy, web, or infrastructure."""

    def test_application_does_not_import_legacy(self):
        for f in _py_files("app/application"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), FORBIDDEN_LEGACY)
                self.assertEqual([], hits, f"{f} imports legacy: {hits}")

    def test_application_does_not_import_web(self):
        for f in _py_files("app/application"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), ("web_app", "web",))
                self.assertEqual([], hits, f"{f} imports web: {hits}")

    def test_application_does_not_import_infrastructure_exporters(self):
        for f in _py_files("app/application"):
            with self.subTest(file=str(f)):
                hits = _any_name_starts(_imports(f), ("app.infrastructure.exporters",))
                self.assertEqual([], hits, f"{f} imports exporters: {hits}")


# ---------------------------------------------------------------------------
# 6. app/core.py white-list (compatibility facade)
# ---------------------------------------------------------------------------


class CoreFacadeWhitelistTests(unittest.TestCase):
    """app/core.py is allowed to import legacy as a compatibility facade."""

    def test_core_may_import_legacy(self):
        f = PROJECT_ROOT / "app" / "core.py"
        if not f.exists():
            self.skipTest("app/core.py not found")
        imps = _imports(f)
        # core.py is explicitly allowed to import legacy
        legacy_hits = _any_name_starts(imps, FORBIDDEN_LEGACY)
        # Not asserting failure — just documenting the allowance
        self.assertTrue(True)  # explicit no-op: facade is permitted

    def test_core_does_not_import_recognition(self):
        f = PROJECT_ROOT / "app" / "core.py"
        if not f.exists():
            self.skipTest("app/core.py not found")
        imps = _imports(f)
        hits = _any_name_starts(imps, ("app.recognition",))
        self.assertEqual(
            [], hits, f"app/core.py must not import recognition: {hits}"
        )


if __name__ == "__main__":
    unittest.main()
