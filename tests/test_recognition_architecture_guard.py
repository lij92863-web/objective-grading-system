"""R14: Architecture guard — recognition must not import legacy/compat/workflow."""
import ast, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecognitionArchitectureGuardTests(unittest.TestCase):
    def test_no_legacy_in_recognition(self):
        for p in (PROJECT_ROOT/"app/recognition").rglob("*.py"):
            src = p.read_text("utf-8")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        self.assertNotIn("legacy", a.name, f"{p.name} imports legacy")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.assertNotIn("legacy", node.module, f"{p.name} imports legacy")
                        self.assertNotIn("app.compat", node.module, f"{p.name} imports compat")
                        self.assertNotIn("app.workflow", node.module, f"{p.name} imports workflow")

    def test_no_workflow_imports_qwen(self):
        for f in ["app/workflow.py", "objective_grader.py"]:
            src = (PROJECT_ROOT/f).read_text("utf-8")
            self.assertNotIn("qwen_adapter", src, f"{f} imports qwen_adapter")


if __name__ == "__main__": unittest.main()
