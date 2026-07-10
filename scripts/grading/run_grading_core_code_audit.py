"""Static release gate for grading-core canonicalization."""

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FAILURES = []


def fail(message):
    FAILURES.append(message)


loader_path = ROOT / "app/infrastructure/loaders/csv_loaders.py"
loader_tree = ast.parse(loader_path.read_text(encoding="utf-8"))
for node in ast.walk(loader_tree):
    if isinstance(node, ast.ClassDef) and node.name in {
        "QuestionSpec", "AnswerKey", "Submission", "QuestionResult", "StudentResult"
    }:
        fail(f"duplicate domain model in loader: {node.name}")

normalize_defs = []
for path in (ROOT / "app").rglob("*.py"):
    if any(part in {
        "legacy", "compat", "answer_extraction", "recognition",
        "student_recognition",
    } for part in path.parts):
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "normalize_answer":
            normalize_defs.append(path.relative_to(ROOT).as_posix())
if normalize_defs != ["app/domain/grading/normalize.py"]:
    fail(f"canonical normalize_answer source violation: {normalize_defs}")

orchestrator_path = ROOT / "app/application/grading/orchestrator.py"
orchestrator_tree = ast.parse(orchestrator_path.read_text(encoding="utf-8"))
run_functions = [
    node
    for node in orchestrator_tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "run_grading_orchestrator"
]
if len(run_functions) != 1 or ast.unparse(run_functions[0].returns) != "GradingRunResult":
    fail("typed orchestrator must return GradingRunResult")
if "Dict[str, object]" in orchestrator_path.read_text(encoding="utf-8"):
    fail("typed orchestrator returns an untyped dict")

workflow_text = (ROOT / "app/workflow.py").read_text(encoding="utf-8")
if "blocked and not allow_errors" in workflow_text:
    fail("allow_errors still bypasses a blocking path")
if "run_grading_orchestrator(request)" not in workflow_text:
    fail("workflow does not use canonical orchestrator")

if FAILURES:
    print("FAIL")
    for item in FAILURES:
        print(f"- {item}")
    sys.exit(1)
print("PASS")
