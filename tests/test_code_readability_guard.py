"""Code readability guard — Stage 3.

Checks that new modules don't contain excessively long physical lines
and that docs are readable (not single-line dumps).
"""

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MAX_LINE_LENGTH = 200

# Files allowed to exceed MAX_LINE_LENGTH (e.g. prompt constants)
LONG_LINE_WHITELIST = {
    "prompts.py",
    "prompt_builder.py",
    # Real client has long f-strings for error messages
    "real_client.py",
    # CSS strings from legacy — single-line compressed, not code
}

HTML_HELPER_ALLOWED_LONG_LINE_FUNCTIONS = {
    "report_css",
    "advanced_dashboard_css",
    "index_css",
}


def _function_line_ranges(path: Path) -> dict[str, range]:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    ranges: dict[str, range] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and hasattr(node, "end_lineno"):
            ranges[node.name] = range(node.lineno, node.end_lineno + 1)
    return ranges


def _is_allowed_long_line(path: Path, lineno: int) -> bool:
    if path.name != "html_helpers.py":
        return False
    ranges = _function_line_ranges(path)
    return any(
        lineno in ranges.get(function_name, range(0))
        for function_name in HTML_HELPER_ALLOWED_LONG_LINE_FUNCTIONS
    )


def _target_files() -> list[Path]:
    dirs = [
        "app/domain",
        "app/recognition",
        "app/application",
        "app/infrastructure",
    ]
    files: list[Path] = []
    for d in dirs:
        files.extend(Path(PROJECT_ROOT, d).rglob("*.py"))
    # also test files
    for pattern in ("test_grading*.py", "test_recognition*.py",
                    "test_qwen*.py", "test_report_builder*.py",
                    "test_*_csv_exporter.py",
                    "test_csv_exporters_migration_matrix.py",
                    "test_report_builders_migration_matrix.py"):
        files.extend(Path(PROJECT_ROOT, "tests").glob(pattern))
    return sorted(files)


def _doc_files() -> list[Path]:
    return sorted(Path(PROJECT_ROOT, "docs").glob("STAGE*.md")) + \
           [PROJECT_ROOT / "docs" / "ANSWER_RECOGNITION_ARCHITECTURE.md"]


class CodeReadabilityGuardTests(unittest.TestCase):
    def test_no_excessively_long_lines(self):
        for f in _target_files():
            if f.name in LONG_LINE_WHITELIST:
                continue
            with self.subTest(file=str(f)):
                long_lines = []
                for lineno, line in enumerate(
                    f.read_text(encoding="utf-8").splitlines(), start=1
                ):
                    if (
                        len(line) > MAX_LINE_LENGTH
                        and not _is_allowed_long_line(f, lineno)
                    ):
                        long_lines.append(lineno)
                self.assertEqual(
                    [], long_lines,
                    f"{f} has lines > {MAX_LINE_LENGTH} chars: {long_lines}"
                )

    def test_markdown_docs_not_single_line(self):
        """Markdown docs must not be a single giant line."""
        for f in _doc_files():
            if not f.exists():
                continue
            with self.subTest(file=str(f)):
                text = f.read_text(encoding="utf-8")
                lines = text.splitlines()
                if len(lines) <= 2 and len(text) > 500:
                    self.fail(
                        f"{f} appears to be a single-line dump "
                        f"({len(text)} chars in {len(lines)} lines)"
                    )

    def test_files_are_utf8(self):
        for f in _target_files():
            with self.subTest(file=str(f)):
                try:
                    f.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    self.fail(f"{f} is not valid UTF-8")


if __name__ == "__main__":
    unittest.main()
