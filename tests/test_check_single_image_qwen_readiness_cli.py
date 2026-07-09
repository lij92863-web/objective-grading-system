import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"
ROI = ROOT / "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class CheckSingleImageQwenReadinessCliTests(unittest.TestCase):
    def test_check_only_passes_without_key(self):
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/check_single_image_qwen_readiness.py"),
            "--manifest", str(MANIFEST), "--roi", str(ROI), "--check-only", "--json",
        ], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(data["valid"])
        self.assertFalse(data["real_api_allowed"])
        self.assertFalse(data["api_key_required"])
        self.assertFalse(data["real_api_called"])


if __name__ == "__main__":
    unittest.main()
