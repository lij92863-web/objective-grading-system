"""Compatibility export parity — C5."""

import unittest

from app.compat.objective_grader_compat import (
    COMPAT_EXPORTS,
    export_compat_symbols,
)


class CompatExportParityTests(unittest.TestCase):

    def test_exports_is_tuple(self):
        self.assertIsInstance(COMPAT_EXPORTS, tuple)

    def test_exports_no_duplicates(self):
        self.assertEqual(len(COMPAT_EXPORTS), len(set(COMPAT_EXPORTS)),
                         "COMPAT_EXPORTS has duplicates")

    def test_export_compat_symbols_returns_dict(self):
        symbols = export_compat_symbols()
        self.assertIsInstance(symbols, dict)

    def test_all_symbols_resolve(self):
        symbols = export_compat_symbols()
        self.assertEqual(len(symbols), len(COMPAT_EXPORTS),
                         f"Missing symbols: "
                         f"{set(COMPAT_EXPORTS) - set(symbols)}")

    def test_spot_check_key_symbols(self):
        """Spot-check that key symbols resolve and are callable/usable."""
        symbols = export_compat_symbols()
        for name in ["load_answer_key", "load_submissions", "grade_all",
                      "write_summary", "write_workbook",
                      "write_simple_report", "item_stats",
                      "create_sample_files"]:
            self.assertIn(name, symbols, f"Missing: {name}")
            self.assertTrue(callable(symbols[name]),
                            f"{name} is not callable")

    def test_compat_module_imports_legacy(self):
        """app/compat is the ONLY app/ module allowed to import legacy."""
        import ast
        from pathlib import Path
        src = (Path(__file__).parents[1] / "app" / "compat"
               / "objective_grader_compat.py").read_text("utf-8")
        self.assertIn("from legacy import", src)

    def test_no_other_allowed_legacy_imports(self):
        """Verify compatibility with main-chain no-legacy gate."""
        import ast
        from pathlib import Path
        root = Path(__file__).parents[1]
        for dir_name in ["app/domain", "app/application",
                         "app/infrastructure", "app/shared"]:
            for f in sorted((root / dir_name).rglob("*.py")):
                tree = ast.parse(f.read_text("utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "legacy" in node.module:
                            self.fail(
                                f"{f} imports legacy: {node.module}")


if __name__ == "__main__":
    unittest.main()
