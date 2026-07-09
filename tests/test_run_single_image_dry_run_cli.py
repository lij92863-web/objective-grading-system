import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"
ROI = ROOT / "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class RunSingleImageDryRunCliTests(unittest.TestCase):
    def test_demo_dry_run(self):
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/run_single_image_dry_run.py"),
            "--manifest", str(MANIFEST), "--roi", str(ROI), "--json",
        ], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(data["valid"])
        self.assertTrue(data["ready_for_qwen_check_only"])
        self.assertFalse(data["ready_for_real_api"])
        self.assertFalse(data["qwen_called"])


if __name__ == "__main__":
    unittest.main()
