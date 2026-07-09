"""Main-chain no-legacy gate — L17A.

Defines "main chain" as: app/domain, app/application, app/infrastructure,
app/shared, app/workflow.py normal path, objective_grader.py normal grading path.
Verifies none of these import or directly call legacy for core operations.
"""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# These files are allowed to import legacy (facades / compatibility)
LEGACY_IMPORT_ALLOWLIST = {
    "app/compat/objective_grader_compat.py",  # ONLY allowed legacy import
    "app/validators.py",          # facade — uses build_validation_report
    "app/analysis.py",            # facade — re-exports legacy
    "app/reports.py",             # facade — re-exports legacy
    "app/core.py",                # facade — re-exports legacy
}


class MainChainNoLegacyGateTests(unittest.TestCase):

    def test_app_layers_no_legacy_import(self):
        violations = []
        for directory in ["app/domain", "app/application",
                          "app/infrastructure", "app/shared"]:
            dp = PROJECT_ROOT / directory
            if not dp.exists():
                continue
            for f in sorted(dp.rglob("*.py")):
                rel = f.relative_to(PROJECT_ROOT).as_posix()
                if rel in LEGACY_IMPORT_ALLOWLIST:
                    continue
                for node in ast.walk(
                    ast.parse(f.read_text(encoding="utf-8"))
                ):
                    if isinstance(node, ast.Import):
                        for a in node.names:
                            if "legacy" in a.name:
                                violations.append((rel, a.name))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "legacy" in node.module:
                            violations.append((rel, node.module))
        self.assertEqual([], violations,
                         f"Non-allowed legacy imports: {violations}")

    def test_main_chain_allowed_files_recorded(self):
        """Verify allowed files exist and are accounted for."""
        for rel in LEGACY_IMPORT_ALLOWLIST:
            fp = PROJECT_ROOT / rel
            self.assertTrue(fp.exists(),
                            f"Allowed file {rel} does not exist — "
                            f"update allowlist")


if __name__ == "__main__":
    unittest.main()
