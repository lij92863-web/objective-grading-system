"""SRE000 global guards (G1-G6).

Static guards that protect the constitution's hard boundaries (no dependency on
``app.workflow`` / ``objective_grader``, no ``grade_all``, no writes to
``submissions.csv`` / ``data/reports``, and a clear four-layer model in the
governing docs). These run without importing business code paths.

Run: python -m unittest discover -s tests/student_recognition
"""

import ast
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_SR_DIR = PROJECT_ROOT / "app" / "student_recognition"
DOCS_SR_DIR = PROJECT_ROOT / "docs" / "student_recognition"

CONSTITUTION = DOCS_SR_DIR / "SRE_GLOBAL_CONSTITUTION.md"
NO_DIRECT = DOCS_SR_DIR / "NO_DIRECT_GRADING_RULES.md"

FOUR_LAYERS = [
    "CaptureJob",
    "RecognitionDraft",
    "TeacherConfirmedSubmission",
    "OfficialGradingInput",
]


def _iter_py_files(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        yield path


def _forbidden_module_imports(target: str) -> list[str]:
    """Return human-readable violations of importing ``target`` under APP_SR_DIR.

    Handles: ``import app.workflow``, ``from app.workflow import ...`` and
    ``from app import workflow`` (equivalently pulls workflow). Same for
    top-level modules such as ``objective_grader``.
    """
    violations: list[str] = []
    parts = target.split(".")
    for path in _iter_py_files(APP_SR_DIR):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            violations.append(f"{path}: syntax error while scanning imports")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == target or alias.name.startswith(target + "."):
                        violations.append(f"{path}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == target:
                    violations.append(f"{path}:{node.lineno}: from {mod} import ...")
                elif len(parts) > 1 and mod == parts[0]:
                    for alias in node.names:
                        if alias.name == parts[1]:
                            violations.append(
                                f"{path}:{node.lineno}: from {mod} import {alias.name}"
                            )
    return violations


def _scan_substring(pattern: str) -> list[str]:
    """Return files (under APP_SR_DIR) whose source contains ``pattern``."""
    hits: list[str] = []
    rx = re.compile(pattern)
    for path in _iter_py_files(APP_SR_DIR):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if rx.search(text):
            hits.append(str(path))
    return hits


class TestGlobalGuards(unittest.TestCase):
    # G1
    def test_no_import_app_workflow(self):
        violations = _forbidden_module_imports("app.workflow")
        self.assertEqual(
            violations, [], f"app/student_recognition must not import app.workflow: {violations}"
        )

    # G2
    def test_no_import_objective_grader(self):
        violations = _forbidden_module_imports("objective_grader")
        self.assertEqual(
            violations,
            [],
            f"app/student_recognition must not import objective_grader: {violations}",
        )

    # G3
    def test_no_grade_all_symbol(self):
        hits = _scan_substring(r"\bgrade_all\b")
        self.assertEqual(hits, [], f"grade_all must not appear in source: {hits}")

    # G4
    def test_no_submissions_csv_write(self):
        hits = _scan_substring(r"submissions\.csv")
        self.assertEqual(hits, [], f"no code may write submissions.csv: {hits}")

    # G5
    def test_no_data_reports_write(self):
        hits = _scan_substring(r"data/reports")
        self.assertEqual(hits, [], f"no code may write data/reports: {hits}")

    # G6
    def test_constitution_distinguishes_four_layers(self):
        self.assertTrue(CONSTITUTION.exists(), "SRE_GLOBAL_CONSTITUTION.md missing")
        self.assertTrue(NO_DIRECT.exists(), "NO_DIRECT_GRADING_RULES.md missing")
        const_text = CONSTITUTION.read_text(encoding="utf-8")
        no_direct_text = NO_DIRECT.read_text(encoding="utf-8")
        combined = const_text + "\n" + no_direct_text
        for layer in FOUR_LAYERS:
            self.assertIn(
                layer,
                combined,
                f"Governing docs must distinguish the layer '{layer}'",
            )


if __name__ == "__main__":
    unittest.main()
