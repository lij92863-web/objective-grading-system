"""Workflow legacy CSV call guard — E7C. Prevents regression."""

import ast, unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_CSV_CALLS = [
    "write_summary", "write_detail", "write_item_analysis",
    "write_knowledge_profiles", "write_practice_recommendations",
    "write_class_report", "write_student_report",
]
# write_validation_report is exempt — it's part of the blocking error path
# Excel calls are now migrated to new exporters — no longer in workflow
ALLOWED_HTML = [
    "write_simple_report", "write_advanced_dashboard", "write_report_index",
]

class WorkflowLegacyCsvCallGuardTests(unittest.TestCase):
    def test_workflow_does_not_call_legacy_csv_write(self):
        f = PROJECT_ROOT/"app/workflow.py"
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for legacy.xxx() or xxx() calls
                func_name = None
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name and func_name in FORBIDDEN_CSV_CALLS:
                    lineno = getattr(node, 'lineno', 0)
                    self.fail(
                        f"workflow.py:{lineno} calls forbidden {func_name}. "
                        f"CSV output must use new pipeline."
                    )

    def test_allowed_html_still_present(self):
        """HTML calls are still allowed (not yet migrated)."""
        text = PROJECT_ROOT.joinpath("app/workflow.py").read_text(encoding="utf-8")
        for name in ALLOWED_HTML:
            self.assertIn(
                name, text,
                f"Expected {name} to still be in workflow.py "
                f"(Excel/HTML not yet migrated)"
            )

if __name__ == "__main__": unittest.main()
