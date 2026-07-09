import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"
ROI = ROOT / "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class RunSingleImageStateSnapshotCliTests(unittest.TestCase):
    def test_snapshot_cli(self):
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/run_single_image_state_snapshot.py"),
            "--manifest", str(MANIFEST), "--roi", str(ROI), "--json",
        ], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["snapshot_type"], "single_image_trial")
        self.assertIn("manifest_summary", data)
        self.assertIn("roi_summary", data)


if __name__ == "__main__":
    unittest.main()
