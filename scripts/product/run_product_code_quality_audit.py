"""Readability and core-object audit for new product modules."""

import ast
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOTS = (
    "app/storage", "app/classes", "app/roster", "app/exam_session",
    "app/capture", "app/product", "app/web_product",
)
FAILURES = []
class_names = []

for source_root in SOURCE_ROOTS:
    for path in (ROOT / source_root).rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        long_lines = [
            index
            for index, line in enumerate(text.splitlines(), start=1)
            if len(line) > 180
        ]
        if long_lines:
            FAILURES.append(f"compressed lines in {path.relative_to(ROOT)}: {long_lines}")
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)
                if node.name == "ProductService":
                    FAILURES.append("god-object ProductService is forbidden")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                if length > 140:
                    FAILURES.append(
                        f"function too long: {path.relative_to(ROOT)}:{node.name} ({length})"
                    )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"execute", "executemany"} and node.args:
                    if isinstance(node.args[0], ast.JoinedStr):
                        relative = path.relative_to(ROOT).as_posix()
                        if relative != "app/storage/repositories.py":
                            FAILURES.append(f"SQL interpolation in {relative}:{node.lineno}")

duplicates = {
    name for name, count in Counter(class_names).items()
    if count > 1 and name in {"Student", "ClassRoom", "ExamSession", "CaptureJob"}
}
if duplicates:
    FAILURES.append(f"duplicate core product models: {sorted(duplicates)}")

if FAILURES:
    print("FAIL")
    for failure in FAILURES:
        print(f"- {failure}")
    sys.exit(1)
print("PASS")
