"""Workflow legacy Excel call guard — E3E. Prevents regression.

After E3E, workflow.py must no longer call legacy Excel write_* functions.
Legacy HTML calls are still allowed (not yet migrated).
"""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# These legacy Excel calls are FORBIDDEN in workflow.py after E3E
FORBIDDEN_EXCEL_CALLS = [
    "write_workbook",
    "write_simple_score_workbook",
    "write_enhanced_workbook",
]

# These legacy HTML calls are still ALLOWED (HTML not yet migrated)
ALLOWED_HTML_CALLS = [
    "write_simple_report",
    "write_advanced_dashboard",
    "write_report_index",
]


class WorkflowLegacyExcelCallGuardTests(unittest.TestCase):
    """workflow.py must route Excel through new exporters, not legacy."""

    def test_workflow_does_not_call_legacy_excel_write(self):
        """Forbid legacy Excel write_* calls in workflow.py."""
        wf = PROJECT_ROOT / "app" / "workflow.py"
        tree = ast.parse(wf.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name and func_name in FORBIDDEN_EXCEL_CALLS:
                    lineno = getattr(node, 'lineno', 0)
                    self.fail(
                        f"workflow.py:{lineno} calls forbidden "
                        f"legacy Excel function '{func_name}'. "
                        f"Excel output must use new exporters."
                    )

    def test_legacy_html_now_migrated(self):
        """Legacy HTML calls are now REMOVED (E4G migrated HTML)."""
        text = (PROJECT_ROOT / "app" / "workflow.py").read_text(
            encoding="utf-8")
        for name in ALLOWED_HTML_CALLS:
            self.assertNotIn(
                name, text,
                f"Legacy HTML call '{name}' should be removed from "
                f"workflow.py after E4G migration"
            )

    def test_workflow_imports_new_exporters(self):
        """Workflow must import the new Excel exporters."""
        text = (PROJECT_ROOT / "app" / "workflow.py").read_text(
            encoding="utf-8")
        self.assertIn("SimpleScoreWorkbookExporter", text,
                      "workflow should import SimpleScoreWorkbookExporter")
        self.assertIn("WorkbookExporter", text,
                      "workflow should import WorkbookExporter")

    def test_workflow_still_imports_legacy(self):
        """D4: workflow NO LONGER imports legacy."""
        text = (PROJECT_ROOT / "app" / "workflow.py").read_text(
            encoding="utf-8")
        self.assertNotIn("from legacy import", text,
                         "workflow should no longer import legacy")


if __name__ == "__main__":
    unittest.main()
