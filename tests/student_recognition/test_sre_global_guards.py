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


def _scan_substring_excluding_docs_comments(pattern: str) -> list[str]:
    """Like ``_scan_substring`` but ignore module/function/class docstrings and
    comments. This lets legitimate prohibition documentation (e.g. a docstring
    that says "must not write submissions.csv") exist without tripping the guard,
    while any *code* that references the pattern is still reported.
    """

    import io
    import tokenize

    rx = re.compile(pattern)
    hits: list[str] = []
    for path in _iter_py_files(APP_SR_DIR):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # Determine lines that are docstrings (Expr whose value is a str constant)
        # or comments, and skip them.
        skip: set[int] = set()
        try:
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    start = node.value.lineno
                    end = getattr(node.value, "end_lineno", start) or start
                    skip.update(range(start, end + 1))
        except SyntaxError:
            # fall through to a raw scan if we cannot parse
            if rx.search(text):
                hits.append(str(path))
            continue
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.COMMENT:
                    skip.update(range(tok.start[0], tok.end[0] + 1))
        except (tokenize.TokenError, IndentationError):
            pass
        for i, line in enumerate(text.splitlines(), 1):
            if i in skip:
                continue
            if rx.search(line):
                hits.append(str(path))
                break
    return hits


def _imports_of_module_prefix(root: Path, prefix: str) -> list[str]:
    """Return violations where any import references ``prefix`` (or its submodules)."""
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == prefix or alias.name.startswith(prefix + "."):
                        violations.append(f"{path}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == prefix or mod.startswith(prefix + "."):
                    violations.append(f"{path}:{node.lineno}: from {mod} import ...")
    return violations


# Free-form status literals that must never appear as a status assignment
# (all status strings must come from state_model.State, constitution §9.1).
_FORBIDDEN_STATUS_LITERALS = {"ok", "done", "finished", "recognised", "success", "complete"}


def _is_status_target(target) -> bool:
    if isinstance(target, ast.Name) and target.id == "status":
        return True
    if isinstance(target, ast.Attribute) and target.attr == "status":
        return True
    return False


def _free_form_status_violations() -> list[str]:
    hits: list[str] = []
    for path in _iter_py_files(APP_SR_DIR):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if _is_status_target(target) and isinstance(node.value, ast.Constant):
                        if isinstance(node.value.value, str) and node.value.value in _FORBIDDEN_STATUS_LITERALS:
                            hits.append(f"{path}:{node.lineno}")
            elif isinstance(node, ast.Dict):
                for key, val in zip(node.keys, node.values):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "status"
                        and isinstance(val, ast.Constant)
                        and isinstance(val.value, str)
                        and val.value in _FORBIDDEN_STATUS_LITERALS
                    ):
                        hits.append(f"{path}:{node.lineno}")
    return hits


def _free_form_error_reason_appends() -> list[str]:
    """Flag ``blocking_errors.append("...")`` or ``review_items.append({"reason":...})``."""
    rx_str = re.compile(r"(blocking_errors|review_items)\.append\(\s*\"")
    rx_dict = re.compile(r"review_items\.append\(\s*\{\s*[\"']?reason")
    hits: list[str] = []
    for path in _iter_py_files(APP_SR_DIR):
        text = path.read_text(encoding="utf-8")
        if rx_str.search(text) or rx_dict.search(text):
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
        hits = _scan_substring_excluding_docs_comments(r"submissions\.csv")
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


    # G7: capture layer must not import omr / grading_bridge (constitution §13)
    def test_capture_does_not_import_omr_or_grading(self):
        capture_dir = APP_SR_DIR / "capture"
        for prefix in (
            "app.student_recognition.omr",
            "app.student_recognition.grading_bridge",
        ):
            violations = _imports_of_module_prefix(capture_dir, prefix)
            self.assertEqual(
                violations,
                [],
                f"capture/ must not import {prefix}: {violations}",
            )

    # G8: pipeline contains no business algorithms (constitution §14)
    def test_pipeline_has_no_business_algorithms(self):
        pipeline_dir = APP_SR_DIR / "pipeline"
        rx = re.compile(
            r"def\s+(locate_page|normalize_image|detect_mark|compute_dark_ratio|"
            r"recognize_omr|crop_roi|threshold_|extract_answer)\s*\("
        )
        hits: list[str] = []
        for path in sorted(pipeline_dir.rglob("*.py")):
            for i, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if rx.search(line):
                    hits.append(f"{path}:{i}")
        self.assertEqual(
            hits, [], f"pipeline/ must not embed business algorithms: {hits}"
        )

    # G9: all status strings come from state_model (constitution §9.1)
    def test_states_only_from_state_model(self):
        violations = _free_form_status_violations()
        self.assertEqual(
            violations, [], f"free-form status literals found: {violations}"
        )

    # G10: errors/reasons only use ErrorCode, never free-form strings (constitution B6)
    def test_errors_only_from_error_codes(self):
        hits = _free_form_error_reason_appends()
        self.assertEqual(
            hits, [], f"free-form error/reason appends found: {hits}"
        )


if __name__ == "__main__":
    unittest.main()
