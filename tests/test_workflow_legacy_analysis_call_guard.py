"""Guard workflow against regressing to legacy analysis helpers."""

import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT_ROOT / "app" / "workflow.py"


class WorkflowLegacyAnalysisCallGuardTests(unittest.TestCase):
    def test_workflow_does_not_call_legacy_analysis_helpers(self):
        tree = ast.parse(WORKFLOW.read_text(encoding="utf-8"))
        forbidden = {"simple_score_rows", "item_stats"}
        hits = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "legacy"
                and func.attr in forbidden
            ):
                hits.append((func.attr, node.lineno))
        self.assertEqual([], hits)

    def test_workflow_imports_application_analysis_builders(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("build_simple_score_rows", text)
        self.assertIn("build_item_stats", text)


if __name__ == "__main__":
    unittest.main()
