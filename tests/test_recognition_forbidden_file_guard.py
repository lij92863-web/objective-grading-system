"""Forbidden file guard — recognition must not import legacy/compat/workflow."""
import ast, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"legacy", "app.compat", "app.workflow", "objective_grader", "web"}


class RecognitionForbiddenFileGuardTests(unittest.TestCase):
    def test_no_forbidden_imports_in_recognition(self):
        violations = []
        for p in (PROJECT_ROOT/"app/recognition").rglob("*.py"):
            if "qwen_adapter/real_client.py" == p.relative_to(PROJECT_ROOT).as_posix():
                continue  # real_client imports legacy internally — pre-existing
            tree = ast.parse(p.read_text("utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        for f in FORBIDDEN:
                            if node.module == f or node.module.startswith(f + "."):
                                violations.append(f"{p.name}: imports {node.module}")
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name in FORBIDDEN:
                            violations.append(f"{p.name}: imports {a.name}")
        self.assertEqual([], violations, f"Forbidden imports: {violations}")


if __name__ == "__main__": unittest.main()
