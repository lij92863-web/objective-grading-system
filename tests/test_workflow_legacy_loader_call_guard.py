"""Guard workflow against regressing to legacy CSV loaders."""

import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT_ROOT / "app" / "workflow.py"


class WorkflowLegacyLoaderCallGuardTests(unittest.TestCase):
    def test_workflow_does_not_call_legacy_loaders(self):
        tree = ast.parse(WORKFLOW.read_text(encoding="utf-8"))
        hits = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "legacy"
                and func.attr in {"load_answer_key", "load_submissions"}
            ):
                hits.append((func.attr, node.lineno))
        self.assertEqual([], hits)


if __name__ == "__main__":
    unittest.main()
