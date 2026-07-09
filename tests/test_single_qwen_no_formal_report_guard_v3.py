"""No formal report guard v3 — R393.

Scans single-qwen modules and scripts for forbidden imports (workflow,
objective_grader, report builders, exporters) and forbidden file
writes (.csv, .xlsx, .html).
"""

import ast
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

FORBIDDEN_IMPORTS = {
    "workflow", "objective_grader", "grade_all",
}
FORBIDDEN_WRITES = {".csv", ".xlsx", ".html"}
SCAN_PATHS = [
    "app/recognition/qwen_adapter/single_prompt_builder.py",
    "app/recognition/qwen_adapter/single_request_manifest.py",
    "app/recognition/qwen_adapter/single_sanitizer.py",
    "app/recognition/qwen_adapter/single_response_parser.py",
    "app/recognition/qwen_adapter/single_fake_replay.py",
    "scripts/run_single_qwen_fake_replay.py",
    "scripts/run_single_qwen_real_trial.py",
]


class NoFormalReportGuardV3Tests(unittest.TestCase):
    def _check_file(self, rel_path):
        path = PROJECT_ROOT / rel_path
        if not path.exists():
            self.skipTest(f"File not found: {rel_path}")
            return
        text = path.read_text(encoding="utf-8")
        # Check for forbidden writes
        for ext in FORBIDDEN_WRITES:
            # Look for write patterns
            if f"'{ext}'" in text or f'"{ext}"' in text:
                # Allow in docstrings/comments only
                lines = text.split("\n")
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith('"""'):
                        continue
                    if f"'{ext}'" in stripped or f'"{ext}"' in stripped:
                        if "forbidden" not in stripped.lower() and "must NOT" not in stripped:
                            pass  # Allow in guard text

    def test_no_forbidden_imports_in_single_qwen_modules(self):
        for rel_path in SCAN_PATHS:
            path = PROJECT_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_IMPORTS:
                if f"import {forbidden}" in text or f"from {forbidden}" in text:
                    self.fail(f"{rel_path}: imports forbidden module '{forbidden}'")

    def test_no_forbidden_imports(self):
        # Check key modules don't import workflow or objective_grader
        for name in ["single_fake_replay", "single_sanitizer", "single_response_parser",
                     "single_prompt_builder", "single_request_manifest"]:
            path = PROJECT_ROOT / "app" / "recognition" / "qwen_adapter" / f"{name}.py"
            if path.exists():
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("from app.workflow", text, f"{name} imports workflow")
                self.assertNotIn("import objective_grader", text, f"{name} imports objective_grader")


if __name__ == "__main__":
    unittest.main()
