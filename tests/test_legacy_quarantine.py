"""Legacy quarantine tests — Stage 5.

Ensures new modules don't import legacy, and legacy doesn't import
new architecture modules.
"""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Allowed to import legacy (compatibility facade)
LEGACY_IMPORT_WHITELIST = {
    PROJECT_ROOT / "app" / "core.py",
    PROJECT_ROOT / "app" / "analysis.py",
    PROJECT_ROOT / "app" / "reports.py",
    PROJECT_ROOT / "app" / "validators.py",
    PROJECT_ROOT / "app" / "workflow.py",
    PROJECT_ROOT / "app" / "data_io.py",
    PROJECT_ROOT / "objective_grader.py",
    PROJECT_ROOT / "grade_exam_workflow.py",
    PROJECT_ROOT / "run_tests.py",
    PROJECT_ROOT / "web_app.py",
    PROJECT_ROOT / "roster_manager.py",
}


def _imports(filepath: Path) -> list[str]:
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


class LegacyQuarantineTests(unittest.TestCase):
    """Lock legacy import boundaries."""

    def test_new_modules_do_not_import_legacy(self):
        new_roots = ("app/domain", "app/recognition")
        for root in new_roots:
            for f in sorted(Path(PROJECT_ROOT, root).rglob("*.py")):
                with self.subTest(file=str(f)):
                    hits = _any_name_starts(_imports(f), ("legacy",))
                    self.assertEqual(
                        [], hits,
                        f"{f} (new module) imports legacy: {hits}"
                    )

    def test_legacy_does_not_import_new_modules(self):
        # legacy may import app.domain.grading (STAGE1 compat bridge)
        # but must NOT import recognition, application, infrastructure, shared
        for f in sorted(Path(PROJECT_ROOT, "legacy").rglob("*.py")):
            with self.subTest(file=str(f)):
                imps = _imports(f)
                hits = _any_name_starts(
                    imps,
                    ("app.recognition", "app.application",
                     "app.infrastructure", "app.shared"),
                )
                self.assertEqual(
                    [], hits,
                    f"{f} (legacy) imports new module: {hits}"
                )

    def test_whitelist_files_exist_and_are_valid(self):
        for f in sorted(LEGACY_IMPORT_WHITELIST):
            if not f.exists():
                continue
            self.assertTrue(
                f.exists(),
                f"Whitelist entry {f} does not exist — "
                f"remove it from LEGACY_IMPORT_WHITELIST"
            )


if __name__ == "__main__":
    unittest.main()
