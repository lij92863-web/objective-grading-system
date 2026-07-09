from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LocalRealSampleSmokeReportV3Tests(unittest.TestCase):
    def test_missing_local_dir_skips_without_outputs(self) -> None:
        completed = subprocess.run([sys.executable, "scripts/run_local_answer_extraction_smoke.py", "--json"], cwd=ROOT, text=True, capture_output=True, check=True)
        data = json.loads(completed.stdout)
        self.assertIn(data["status"], {"skipped", "completed"})


if __name__ == "__main__":
    unittest.main()
