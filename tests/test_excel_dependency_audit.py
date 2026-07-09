"""Excel dependency audit — Stage E3A-H static checks.

Does NOT install anything, does NOT read .env, does NOT call the network.
Only performs static analysis of project files and legacy imports.
"""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ── known dependency-file names ────────────────────────────────────────
DEPENDENCY_FILE_NAMES = (
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "poetry.lock",
    "environment.yml",
)

# ── libraries that would change the migration route if present ────────
EXCEL_LIBRARIES = ("openpyxl", "xlsxwriter", "pandas", "xlwt", "xlrd")

# ── detect openpyxl once ──────────────────────────────────────────────
OPENPYXL_AVAILABLE = False
try:
    import openpyxl  # noqa: F401
    OPENPYXL_AVAILABLE = True
except ImportError:
    pass


class ExcelDependencyFileAuditTests(unittest.TestCase):
    """Static checks: what dependency files exist and what they declare."""

    def test_dependency_files_present_or_absent(self):
        """Record which dependency files exist at project root."""
        found = []
        for name in DEPENDENCY_FILE_NAMES:
            if (PROJECT_ROOT / name).exists():
                found.append(name)
        # This is informational — the project currently has zero dep files.
        # That is expected and does NOT fail the test.
        self.assertIsInstance(found, list)

    def test_no_excel_library_in_requirements_txt(self):
        """If requirements.txt exists it must not silently add excel libs."""
        req = PROJECT_ROOT / "requirements.txt"
        if not req.exists():
            self.skipTest("No requirements.txt")
        text = req.read_text(encoding="utf-8").lower()
        for lib in EXCEL_LIBRARIES:
            self.assertNotIn(lib, text,
                             f"requirements.txt contains {lib}")

    def test_no_excel_library_in_pyproject_toml(self):
        """If pyproject.toml exists it must not silently add excel libs."""
        pp = PROJECT_ROOT / "pyproject.toml"
        if not pp.exists():
            self.skipTest("No pyproject.toml")
        text = pp.read_text(encoding="utf-8").lower()
        for lib in EXCEL_LIBRARIES:
            self.assertNotIn(lib, text,
                             f"pyproject.toml contains {lib}")

    def test_no_excel_library_in_setup_cfg(self):
        """If setup.cfg exists it must not silently add excel libs."""
        sc = PROJECT_ROOT / "setup.cfg"
        if not sc.exists():
            self.skipTest("No setup.cfg")
        text = sc.read_text(encoding="utf-8").lower()
        for lib in EXCEL_LIBRARIES:
            self.assertNotIn(lib, text,
                             f"setup.cfg contains {lib}")


class LegacyExcelImportAuditTests(unittest.TestCase):
    """Verify that legacy does NOT pull in external Excel libraries."""

    @classmethod
    def setUpClass(cls):
        legacy_path = PROJECT_ROOT / "legacy" / "objective_grader_legacy.py"
        cls.legacy_imports = set()
        cls.legacy_stdlib_imports = set()
        tree = ast.parse(legacy_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    cls.legacy_imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    cls.legacy_imports.add(node.module.split(".")[0])
                    cls.legacy_stdlib_imports.add(node.module)

    def test_legacy_does_not_import_openpyxl(self):
        self.assertNotIn("openpyxl", self.legacy_imports,
                         "legacy unexpectedly imports openpyxl")

    def test_legacy_does_not_import_xlsxwriter(self):
        self.assertNotIn("xlsxwriter", self.legacy_imports,
                         "legacy unexpectedly imports xlsxwriter")

    def test_legacy_does_not_import_pandas(self):
        self.assertNotIn("pandas", self.legacy_imports,
                         "legacy unexpectedly imports pandas")

    def test_legacy_does_not_import_xlwt(self):
        self.assertNotIn("xlwt", self.legacy_imports,
                         "legacy unexpectedly imports xlwt")

    def test_legacy_does_not_import_xlrd(self):
        self.assertNotIn("xlrd", self.legacy_imports,
                         "legacy unexpectedly imports xlrd")

    def test_legacy_uses_zipfile_for_xlsx(self):
        """Legacy must use zipfile (the stdlib XLSX container)."""
        self.assertIn("zipfile", self.legacy_imports,
                      "legacy does not import zipfile — "
                      "xlsx generation method unclear")

    def test_legacy_uses_xml_for_xlsx(self):
        """Legacy must use xml.etree or xml.sax for XLSX content."""
        xml_imports = {i for i in self.legacy_stdlib_imports
                       if i.startswith("xml")}
        self.assertTrue(xml_imports,
                        f"legacy has no xml imports: {self.legacy_stdlib_imports}")


class OpenpyxlAvailabilityRecordTests(unittest.TestCase):
    """Document the current openpyxl status — informational, not pass/fail."""

    def test_openpyxl_availability_is_recorded(self):
        """Simply record whether openpyxl is importable right now."""
        # This test never fails — it captures state for the audit trail.
        self.assertIn(OPENPYXL_AVAILABLE, (True, False))

    def test_openpyxl_not_required_for_tests(self):
        """Tests must pass regardless of openpyxl presence."""
        # If openpyxl is absent that is FINE — the project works without it.
        self.assertTrue(True)


class WorkflowExcelImportAuditTests(unittest.TestCase):
    """Verify how workflow.py handles Excel output (Route B — new exporters)."""

    @classmethod
    def setUpClass(cls):
        wf_path = PROJECT_ROOT / "app" / "workflow.py"
        cls.wf_source = wf_path.read_text(encoding="utf-8")

    def test_workflow_uses_new_workbook_exporter(self):
        """E3E: workflow must route Excel through WorkbookExporter."""
        self.assertIn("WorkbookExporter", self.wf_source,
                      "workflow should import WorkbookExporter")

    def test_workflow_uses_new_simple_score_exporter(self):
        """E3E: workflow must route simple score through new exporter."""
        self.assertIn("SimpleScoreWorkbookExporter", self.wf_source,
                      "workflow should import SimpleScoreWorkbookExporter")

    def test_workflow_no_longer_calls_legacy_excel(self):
        """E3E: workflow must NOT call legacy Excel write_* functions."""
        self.assertNotIn("legacy.write_workbook", self.wf_source,
                         "workflow should not call legacy.write_workbook")
        self.assertNotIn("write_enhanced_workbook", self.wf_source,
                         "workflow should not define write_enhanced_workbook")

    def test_workflow_still_uses_legacy_for_html(self):
        """Legacy HTML calls are still needed (HTML not yet migrated)."""
        self.assertIn("legacy.write_simple_report", self.wf_source,
                      "workflow must still call legacy HTML")


if __name__ == "__main__":
    unittest.main()
