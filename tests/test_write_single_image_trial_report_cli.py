import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"
ROI = ROOT / "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class WriteSingleImageTrialReportCliTests(unittest.TestCase):
    def test_stdout_report_is_safe(self):
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/write_single_image_trial_report.py"),
            "--manifest", str(MANIFEST), "--roi", str(ROI), "--json",
        ], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertFalse(data["real_api_called"])
        self.assertFalse(data["raw_response_saved"])
        self.assertFalse(data["base64_emitted"])


if __name__ == "__main__":
    unittest.main()
