"""Dependency-direction and grading-order audit."""

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FAILURES = []


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.append(node.module or "")
    return found


for path in (ROOT / "app/domain/grading").glob("*.py"):
    for module in imports(path):
        if module.startswith(("app.infrastructure", "app.workflow", "web")):
            FAILURES.append(f"domain dependency inversion: {path.name} -> {module}")

loader_imports = imports(ROOT / "app/infrastructure/loaders/csv_loaders.py")
if not any(module.startswith("app.domain.grading") for module in loader_imports):
    FAILURES.append("CSV loader does not depend on canonical domain")

orchestrator = (ROOT / "app/application/grading/orchestrator.py").read_text(encoding="utf-8")
precheck_at = orchestrator.find("run_grading_precheck(")
grade_at = orchestrator.find("grade_all(")
if precheck_at < 0 or grade_at < 0 or precheck_at >= grade_at:
    FAILURES.append("precheck is not ordered before grade_all")
if "if not precheck.can_grade" not in orchestrator[precheck_at:grade_at]:
    FAILURES.append("grade_all is not guarded by precheck.can_grade")

for path in [ROOT / "app/application/grading/contracts.py", ROOT / "app/application/grading/orchestrator.py"]:
    text = path.read_text(encoding="utf-8")
    if "app.recognition" in text or "app.student_recognition" in text:
        FAILURES.append(f"new recognition dependency in {path.name}")

if FAILURES:
    print("FAIL")
    for item in FAILURES:
        print(f"- {item}")
    sys.exit(1)
print("PASS")
