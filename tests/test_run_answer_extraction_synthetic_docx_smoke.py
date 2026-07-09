from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RunAnswerExtractionSyntheticDocxSmokeTests(unittest.TestCase):
    def test_smoke_outputs_cases(self) -> None:
        completed = subprocess.run([sys.executable, "scripts/run_answer_extraction_synthetic_docx_smoke.py", "--json"], cwd=ROOT, text=True, capture_output=True, check=True)
        data = json.loads(completed.stdout)
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["case_count"], 8)
        self.assertTrue(any(run["case_id"] == "same_file_itemized_real_brackets" for run in data["runs"]))


if __name__ == "__main__":
    unittest.main()
