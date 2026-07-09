import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_CALLS = {
    "build_knowledge_profiles",
    "build_validation_report",
    "basic_stats",
}


class WorkflowRemainingLegacyBuilderGuardTests(unittest.TestCase):
    def test_workflow_does_not_call_remaining_legacy_builders(self):
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
                and func.attr in FORBIDDEN_CALLS
            ):
                self.fail(f"workflow.py:{node.lineno} calls legacy.{func.attr}")


if __name__ == "__main__":
    unittest.main()
