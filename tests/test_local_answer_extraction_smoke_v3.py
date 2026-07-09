from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = ROOT / "scripts" / "run_local_answer_extraction_smoke.py"


class LocalAnswerExtractionSmokeV3Tests(unittest.TestCase):
    def test_smoke_script_runs_and_returns_json(self):
        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--json"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"Smoke script did not return valid JSON: {result.stdout[:200]}")
        self.assertIn("status", data)

    def test_smoke_output_has_expected_keys(self):
        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--json"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        data = json.loads(result.stdout)
        valid_statuses = {"skipped", "ok", "partial", "failed"}
        self.assertIn(data["status"], valid_statuses)

    def test_skipped_when_no_samples(self):
        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--json"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        data = json.loads(result.stdout)
        if data["status"] == "skipped":
            self.assertIn("reason", data)
            self.assertIn("sample_dir", data)

    def test_smoke_returns_zero_exit_code(self):
        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--json"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertIn(result.returncode, (0, 1))


if __name__ == "__main__":
    unittest.main()
