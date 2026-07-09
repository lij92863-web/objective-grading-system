"""Workflow legacy HTML call guard — E4G. Prevents regression to legacy HTML."""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# After E4G, workflow must NOT call these legacy write_* functions
FORBIDDEN_CALLS = [
    # HTML (E4G)
    "write_simple_report",
    "write_advanced_dashboard",
    "write_report_index",
    # Excel (E3E)
    "write_workbook",
    "write_simple_score_workbook",
    "write_enhanced_workbook",
    # CSV (E7)
    "write_summary",
    "write_detail",
    "write_item_analysis",
    "write_knowledge_profiles",
    "write_practice_recommendations",
    "write_class_report",
    "write_student_report",
]


class WorkflowLegacyHtmlCallGuardTests(unittest.TestCase):

    def test_workflow_does_not_call_any_legacy_write(self):
        wf = PROJECT_ROOT / "app" / "workflow.py"
        tree = ast.parse(wf.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name and func_name in FORBIDDEN_CALLS:
                    lineno = getattr(node, 'lineno', 0)
                    self.fail(
                        f"workflow.py:{lineno} calls forbidden "
                        f"'{func_name}'. Must use new exporters."
                    )

    def test_workflow_imports_html_exporters(self):
        text = (PROJECT_ROOT / "app" / "workflow.py").read_text(
            encoding="utf-8")
        for name in ["SimpleReportHtmlExporter",
                      "AdvancedDashboardHtmlExporter",
                      "ReportIndexHtmlExporter"]:
            self.assertIn(name, text,
                          f"workflow missing import: {name}")

    def test_workflow_still_imports_legacy(self):
        text = (PROJECT_ROOT / "app" / "workflow.py").read_text(
            encoding="utf-8")
        self.assertIn("from legacy import", text,
                      "workflow should still import legacy for data")


if __name__ == "__main__":
    unittest.main()
