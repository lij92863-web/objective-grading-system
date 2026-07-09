"""Tests for real Qwen trial runner gate — R374."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SCRIPT = str(PROJECT_ROOT / "scripts" / "run_single_qwen_real_trial.py")


class RunSingleQwenRealTrialGateTests(unittest.TestCase):
    def _run(self, *extra_args):
        return subprocess.run(
            [sys.executable, SCRIPT, "--json", *extra_args],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )

    def test_default_fail_closed(self):
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertFalse(data["gates_passed"])
        self.assertFalse(data["real_api_called"])

    def test_missing_allow_real_api_fails(self):
        result = self._run("--confirm-anonymous", "--check-only-passed",
                          "--api-key-env", "QWEN_API_KEY")
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("MISSING_ALLOW_REAL_API", data["blockers"])

    def test_missing_confirm_anonymous_fails(self):
        result = self._run("--allow-real-api", "--check-only-passed",
                          "--api-key-env", "QWEN_API_KEY")
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("MISSING_CONFIRM_ANONYMOUS", data["blockers"])

    def test_missing_check_only_passed_fails(self):
        result = self._run("--allow-real-api", "--confirm-anonymous",
                          "--api-key-env", "QWEN_API_KEY")
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("MISSING_CHECK_ONLY_PASSED", data["blockers"])

    def test_missing_api_key_env_fails(self):
        result = self._run("--allow-real-api", "--confirm-anonymous",
                          "--check-only-passed")
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("MISSING_API_KEY_ENV", data["blockers"])

    def test_save_raw_response_true_fails(self):
        result = self._run("--allow-real-api", "--confirm-anonymous",
                          "--check-only-passed", "--api-key-env", "QWEN_API_KEY",
                          "--save-raw-response")
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("SAVE_RAW_RESPONSE_MUST_BE_FALSE", data["blockers"])

    def test_emit_base64_true_fails(self):
        result = self._run("--allow-real-api", "--confirm-anonymous",
                          "--check-only-passed", "--api-key-env", "QWEN_API_KEY",
                          "--emit-base64")
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("EMIT_BASE64_MUST_BE_FALSE", data["blockers"])

    def test_max_calls_exceeds_one_fails(self):
        result = self._run("--allow-real-api", "--confirm-anonymous",
                          "--check-only-passed", "--api-key-env", "QWEN_API_KEY",
                          "--max-calls", "2")
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(any("MAX_CALLS" in b for b in data["blockers"]))

    def test_no_actual_api_call_in_tests(self):
        result = self._run("--allow-real-api", "--confirm-anonymous",
                          "--check-only-passed", "--api-key-env", "QWEN_API_KEY")
        data = json.loads(result.stdout)
        self.assertFalse(data["real_api_called"])

    def test_no_env_read_in_gate(self):
        result = self._run("--allow-real-api", "--confirm-anonymous",
                          "--check-only-passed", "--api-key-env", "QWEN_API_KEY")
        data = json.loads(result.stdout)
        self.assertFalse(data["env_read"])


if __name__ == "__main__":
    unittest.main()
