"""No real API default guard v6 — R394."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SCRIPTS = [
    "build_single_qwen_request_manifest.py",
    "run_single_qwen_fake_replay.py",
    "run_single_qwen_real_trial.py",
    "write_single_real_trial_not_executed_report.py",
    "run_single_qwen_fake_replay_snapshot.py",
]


class NoRealApiDefaultGuardV6Tests(unittest.TestCase):
    def _run_script(self, script_name, *extra_args):
        script_path = PROJECT_ROOT / "scripts" / script_name
        if not script_path.exists():
            self.skipTest(f"Script not found: {script_name}")
            return None
        result = subprocess.run(
            [sys.executable, str(script_path), "--json", *extra_args],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        return result

    def test_build_request_manifest_no_real_api(self):
        result = self._run_script(
            "build_single_qwen_request_manifest.py",
            "--manifest", "tests/fixtures/recognition/single_image/demo_single_image_manifest.json",
            "--roi", "tests/fixtures/recognition/single_image/demo_manual_roi.json",
        )
        if result is None:
            return
        data = json.loads(result.stdout)
        self.assertFalse(data.get("real_api_allowed", True))
        self.assertFalse(data.get("qwen_called", True))
        self.assertFalse(data.get("env_read", True))

    def test_fake_replay_no_real_api(self):
        result = self._run_script(
            "run_single_qwen_fake_replay.py",
            "--manifest", "tests/fixtures/recognition/single_image/demo_single_image_manifest.json",
            "--roi", "tests/fixtures/recognition/single_image/demo_manual_roi.json",
            "--fake-response", "tests/fixtures/recognition/qwen_single_response/fake_single_qwen_valid_choice_blank_identity.json",
        )
        if result is None:
            return
        data = json.loads(result.stdout)
        self.assertFalse(data.get("real_api_called", True))
        self.assertFalse(data.get("qwen_called", True))

    def test_real_trial_default_fail_closed(self):
        result = self._run_script("run_single_qwen_real_trial.py")
        if result is None:
            return
        self.assertNotEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertFalse(data.get("real_api_called", True))

    def test_not_executed_report_no_real_api(self):
        result = self._run_script("write_single_real_trial_not_executed_report.py")
        if result is None:
            return
        data = json.loads(result.stdout)
        self.assertFalse(data.get("real_api_called", True))

    def test_snapshot_no_real_api(self):
        result = self._run_script(
            "run_single_qwen_fake_replay_snapshot.py",
            "--manifest", "tests/fixtures/recognition/single_image/demo_single_image_manifest.json",
            "--roi", "tests/fixtures/recognition/single_image/demo_manual_roi.json",
            "--fake-response", "tests/fixtures/recognition/qwen_single_response/fake_single_qwen_valid_choice_blank_identity.json",
        )
        if result is None:
            return
        data = json.loads(result.stdout)
        self.assertFalse(data.get("real_api_called", True))


if __name__ == "__main__":
    unittest.main()
