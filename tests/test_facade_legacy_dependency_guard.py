"""Facade legacy dependency guard — C11/C12."""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FACADE_FILES = [
    "app/analysis.py",
    "app/reports.py",
    "app/core.py",
    "app/validators.py",
]


class FacadeLegacyDependencyGuardTests(unittest.TestCase):

    def test_facade_files_exist(self):
        for f in FACADE_FILES:
            self.assertTrue((PROJECT_ROOT / f).exists(),
                            f"Missing facade: {f}")

    def test_facade_files_do_not_direct_import_legacy(self):
        """C12: facades must NOT import legacy directly."""
        violations = []
        for f in FACADE_FILES:
            src = (PROJECT_ROOT / f).read_text("utf-8")
            if "from legacy.objective_grader_legacy import" in src:
                violations.append(f)
        self.assertEqual([], violations,
                         f"Facades still import legacy directly: {violations}")

    def test_facade_files_public_symbols_still_resolve(self):
        """All public symbols from facades must still be importable."""
        for f in FACADE_FILES:
            mod_path = f.replace("/", ".").replace(".py", "")
            try:
                __import__(mod_path)
            except ImportError as e:
                self.fail(f"Failed to import {mod_path}: {e}")


if __name__ == "__main__":
    unittest.main()
