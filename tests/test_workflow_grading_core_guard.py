import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WorkflowGradingCoreGuardTests(unittest.TestCase):
    def test_workflow_does_not_call_legacy_grade_all(self):
        source_path = PROJECT_ROOT / "app/workflow.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "legacy"
                and func.attr == "grade_all"
            ):
                self.fail(f"workflow.py:{node.lineno} calls legacy.grade_all")

    def test_workflow_imports_domain_grade_all(self):
        text = (PROJECT_ROOT / "app/workflow.py").read_text(encoding="utf-8")
        self.assertIn("from app.domain.grading import grade_all", text)


if __name__ == "__main__":
    unittest.main()
