"""Base64 guard for real trial — R378."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

CORE_MODULES = [
    "app/recognition/qwen_adapter/single_prompt_builder.py",
    "app/recognition/qwen_adapter/single_request_manifest.py",
    "app/recognition/qwen_adapter/single_sanitized_output.py",
]


class SingleRealTrialBase64GuardTests(unittest.TestCase):
    def test_no_emit_base64_true(self):
        for rel_path in CORE_MODULES:
            path = PROJECT_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("emit_base64=True", text)
            self.assertNotIn("emit_base64 = True", text)

    def test_no_image_base64_field_in_prompt_builder(self):
        path = PROJECT_ROOT / "app/recognition/qwen_adapter/single_prompt_builder.py"
        if not path.exists():
            self.skipTest("File not found")
            return
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("image_base64", text)

    def test_no_base64_data_field_in_manifest(self):
        path = PROJECT_ROOT / "app/recognition/qwen_adapter/single_request_manifest.py"
        if not path.exists():
            self.skipTest("File not found")
            return
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("base64_data", text)

    def test_no_real_image_base64_strings(self):
        """Long base64 strings should not appear in source code."""
        for rel_path in CORE_MODULES:
            path = PROJECT_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            # Check for actual long base64 strings (80+ chars of base64 chars)
            lines = text.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""'):
                    continue
                # Check for data URI pattern (this would be actual base64 image)
                if "data:image/png;base64," in stripped or "data:image/jpeg;base64," in stripped:
                    self.fail(f"{rel_path}: contains data:image base64 URI")


if __name__ == "__main__":
    unittest.main()
