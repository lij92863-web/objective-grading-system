"""SRE945 §15.9 -- dependency / constitution guards for the template packages.

Protects the hard boundaries (constitution B4/B5/B10/§13):
  * ``template/**`` and ``template_builder/**`` must NOT import ``omr``,
    ``image``, ``grading_bridge``, ``web_app`` or ``flask``.
  * No ``PIL`` / ``cv2`` / ``numpy`` dependency (B4).

Reuses the AST-scan technique from ``test_sre_global_guards.py`` but scopes it to
the two SRE945 packages. Imports of ``synthetic`` / ``errors`` / ``common`` /
``state`` / ``coordinates`` are explicitly allowed.
"""

import ast
import io
import tokenize
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_SR_DIR = PROJECT_ROOT / "app" / "student_recognition"
TEMPLATE_DIR = APP_SR_DIR / "template"
BUILDER_DIR = APP_SR_DIR / "template_builder"

# Modules that must never be imported by the template packages.
FORBIDDEN_MODULES = (
    "omr",
    "image",
    "grading_bridge",
    "web_app",
    "flask",
    "PIL",
    "cv2",
    "numpy",
)


def _iter_py_files(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        yield path


def _module_import_violations() -> list:
    violations = []
    for root in (TEMPLATE_DIR, BUILDER_DIR):
        for path in _iter_py_files(root):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                violations.append(f"{path}: syntax error")
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in FORBIDDEN_MODULES or any(
                            alias.name == m or alias.name.startswith(m + ".")
                            for m in FORBIDDEN_MODULES
                        ):
                            violations.append(f"{path}:{node.lineno}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    top = mod.split(".")[0]
                    if top in FORBIDDEN_MODULES:
                        violations.append(f"{path}:{node.lineno}: from {mod} import ...")
    return violations


def _scan_substring_excluding_docs_comments(pattern: str) -> list:
    """Return files (under the two SRE945 dirs) whose *code* contains ``pattern``.

    Docstrings and comments are skipped so prohibited words may appear in
    explanatory prose without tripping the guard.
    """
    import re

    rx = re.compile(pattern)
    hits = []
    for root in (TEMPLATE_DIR, BUILDER_DIR):
        for path in _iter_py_files(root):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            skip = set()
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


class TestTemplateBuilderGuards(unittest.TestCase):
    def test_template_builder_does_not_import_omr(self):
        hits = [
            v
            for v in _module_import_violations()
            if "omr" in v
        ]
        self.assertEqual(hits, [], f"template packages must not import omr: {hits}")

    def test_template_builder_does_not_import_image(self):
        hits = [v for v in _module_import_violations() if "image" in v]
        self.assertEqual(hits, [], f"template packages must not import image: {hits}")

    def test_template_builder_does_not_import_grading(self):
        hits = [v for v in _module_import_violations() if "grading_bridge" in v]
        self.assertEqual(
            hits, [], f"template packages must not import grading_bridge: {hits}"
        )

    def test_template_builder_does_not_import_web_app(self):
        hits = [
            v for v in _module_import_violations() if ("web_app" in v or "flask" in v)
        ]
        self.assertEqual(
            hits, [], f"template packages must not import web_app/flask: {hits}"
        )

    def test_template_builder_has_no_pil_opencv_numpy_dependency(self):
        # Real import statements of the forbidden libs.
        import_hits = [
            v
            for v in _module_import_violations()
            if any(lib in v for lib in ("PIL", "cv2", "numpy"))
        ]
        self.assertEqual(
            import_hits, [], f"no PIL/cv2/numpy imports allowed: {import_hits}"
        )
        # Also forbid the bare tokens appearing in *code* (not docstrings/comments).
        for lib in ("PIL", "cv2", "numpy"):
            code_hits = _scan_substring_excluding_docs_comments(rf"\b{lib}\b")
            self.assertEqual(
                code_hits, [], f"{lib} must not appear in template package code"
            )


if __name__ == "__main__":
    unittest.main()
