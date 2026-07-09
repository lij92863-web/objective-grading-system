"""API key guard for real trial — R379."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

CORE_MODULES = [
    "app/recognition/qwen_adapter/single_trial_config.py",
    "app/recognition/qwen_adapter/single_request_manifest.py",
    "app/recognition/qwen_adapter/single_sanitized_output.py",
    "app/recognition/single_real_trial_not_executed_report.py",
]


class SingleRealTrialApiKeyGuardTests(unittest.TestCase):
    def test_api_key_env_is_name_only(self):
        path = PROJECT_ROOT / "app/recognition/qwen_adapter/single_trial_config.py"
        if not path.exists():
            self.skipTest("File not found")
            return
        text = path.read_text(encoding="utf-8")
        self.assertIn("env var", text.lower())

    def test_no_key_value_assignment(self):
        for rel_path in CORE_MODULES:
            path = PROJECT_ROOT / rel_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            lines = text.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""'):
                    continue
                # Check for hardcoded key-like values
                if "sk-" in stripped and ("=" in stripped or ":" in stripped):
                    # Only fail if it's an actual assignment of a key value
                    if "api_key" in stripped.lower() and '"sk-' in stripped:
                        self.fail(f"{rel_path}: hardcoded key: {stripped[:80]}")

    def test_no_key_in_not_executed_report(self):
        path = PROJECT_ROOT / "app/recognition/single_real_trial_not_executed_report.py"
        if not path.exists():
            self.skipTest("File not found")
            return
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue
            if "sk-" in stripped and ("=" in stripped or ":" in stripped):
                self.fail(f"not_executed_report: possible key: {stripped[:80]}")

    def test_no_printing_key_in_scripts(self):
        path = PROJECT_ROOT / "scripts/run_single_qwen_real_trial.py"
        if not path.exists():
            self.skipTest("Script not found")
            return
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("print(key", text)
        self.assertNotIn("print(api_key", text)

    def test_env_not_read_directly(self):
        path = PROJECT_ROOT / "scripts/run_single_qwen_real_trial.py"
        if not path.exists():
            self.skipTest("Script not found")
            return
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("dotenv", text.lower())
        self.assertNotIn("load_dotenv", text.lower())


if __name__ == "__main__":
    unittest.main()
