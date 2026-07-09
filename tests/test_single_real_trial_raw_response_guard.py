"""Raw response guard for real trial — R377."""
import ast
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SCAN_FILES = [
    "scripts/run_single_qwen_real_trial.py",
    "app/recognition/qwen_adapter/single_sanitizer.py",
    "app/recognition/qwen_adapter/single_sanitized_output.py",
    "app/recognition/single_image_trial_report.py",
]


class SingleRealTrialRawResponseGuardTests(unittest.TestCase):
    def test_no_save_raw_response_path(self):
        for rel_path in SCAN_FILES:
            path = PROJECT_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            lines = text.split("\n")
            for lineno, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                # Only check for actual file-write patterns
                if "raw_response" in stripped.lower():
                    if ".write" in stripped or "open(" in stripped or "path.write" in stripped:
                        if "raw_response_saved" not in stripped:
                            self.fail(f"{rel_path}:{lineno}: writes raw_response: {stripped[:80]}")

    def test_raw_response_saved_field_is_false(self):
        for rel_path in SCAN_FILES:
            path = PROJECT_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            # raw_response_saved should only appear as False or in prohibition text
            self.assertNotIn('raw_response_saved=True', text, f"{rel_path} sets raw_response_saved=True")
            self.assertNotIn('raw_response_saved = True', text, f"{rel_path} sets raw_response_saved=True")

    def test_no_file_writes_named_raw_response(self):
        for rel_path in SCAN_FILES:
            path = PROJECT_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("raw_response.json", text.lower())
            self.assertNotIn("raw_response.txt", text.lower())


if __name__ == "__main__":
    unittest.main()
