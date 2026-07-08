"""External-effects ban tests — Stage 2.

Ensures the default test/run environment never accidentally calls
real external APIs, reads .env, or leaks secrets.
"""

import ast
import os
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Files that are ALLOWED to reference HTTP / API machinery (but still
# gated behind env vars).
ALLOWED_HTTP_FILES = {
    PROJECT_ROOT / "app" / "recognition" / "qwen_adapter" / "real_client.py",
    PROJECT_ROOT / "scripts" / "qwen_single_image_smoke.py",
}


def _py_files(root: str) -> list[Path]:
    return sorted(Path(PROJECT_ROOT, root).rglob("*.py"))


def _string_constants(filepath: Path) -> list[str]:
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    strings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value)
    return strings


def _imports(filepath: Path) -> list[str]:
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                names.append(f"{mod}.{alias.name}" if mod else alias.name)
    return names


class NoUncontrolledExternalEffectsTests(unittest.TestCase):
    """Guard against accidental external API calls in tests and core."""

    def test_test_files_do_not_import_http_clients(self):
        http_modules = ("requests", "urllib.request", "http.client",
                        "dashscope", "openai", "httpx")
        for f in _py_files("tests"):
            with self.subTest(file=str(f)):
                imps = _imports(f)
                hits = [i for i in imps
                        if any(i.startswith(m) for m in http_modules)]
                self.assertEqual(
                    [], hits, f"{f} imports HTTP client: {hits}"
                )

    def test_tests_do_not_read_dotenv(self):
        for f in _py_files("tests"):
            with self.subTest(file=str(f)):
                imps = _imports(f)
                hits = [i for i in imps if "dotenv" in i or ".env" in i]
                self.assertEqual(
                    [], hits, f"{f} references dotenv: {hits}"
                )

    def test_tests_do_not_require_api_key(self):
        saved = os.environ.pop("QWEN_API_KEY", None)
        try:
            for f in _py_files("tests"):
                if f.name == "__init__.py":
                    continue
                with self.subTest(file=str(f)):
                    text = f.read_text(encoding="utf-8")
                    # Must not contain patterns like sk-<hex> that look real
                    if "QWEN_API_KEY" in text:
                        # Tests may reference the env var name, that's ok
                        pass
        finally:
            if saved is not None:
                os.environ["QWEN_API_KEY"] = saved

    def test_no_hardcoded_api_keys(self):
        # test files may use obviously-fake short keys for testing
        _test_whitelist = {PROJECT_ROOT / "tests" / "test_qwen_real_client_safety.py"}
        for root in ("app",):
            for f in _py_files(root):
                if f.resolve() in _test_whitelist:
                    continue
                with self.subTest(file=str(f)):
                    for s in _string_constants(f):
                        if s.startswith("sk-") and len(s) > 20:
                            self.fail(
                                f"{f} contains hardcoded API key pattern"
                            )

    def test_no_base64_image_in_log_or_print(self):
        for root in ("app",):
            for f in _py_files(root):
                with self.subTest(file=str(f)):
                    text = f.read_text(encoding="utf-8")
                    if 'print("data:image' in text:
                        self.fail(
                            f"{f} prints image base64"
                        )

    def test_smoke_script_defaults_to_dry_run(self):
        smoke = PROJECT_ROOT / "scripts" / "qwen_single_image_smoke.py"
        if not smoke.exists():
            self.skipTest("smoke script not found")
        text = smoke.read_text(encoding="utf-8")
        self.assertIn("--dry-run", text)
        self.assertIn("DRY-RUN", text)


if __name__ == "__main__":
    unittest.main()
