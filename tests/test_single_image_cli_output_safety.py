import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"
ROI = ROOT / "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class SingleImageCliOutputSafetyTests(unittest.TestCase):
    def test_cli_outputs_do_not_expose_forbidden_content(self):
        commands = [
            [sys.executable, str(ROOT / "scripts/validate_single_image_manifest.py"), "--manifest", str(MANIFEST), "--json"],
            [sys.executable, str(ROOT / "scripts/validate_manual_roi.py"), "--roi", str(ROI), "--json"],
            [sys.executable, str(ROOT / "scripts/run_single_image_dry_run.py"), "--manifest", str(MANIFEST), "--roi", str(ROI), "--json"],
            [sys.executable, str(ROOT / "scripts/check_single_image_qwen_readiness.py"), "--manifest", str(MANIFEST), "--roi", str(ROI), "--check-only", "--json"],
            [sys.executable, str(ROOT / "scripts/write_single_image_trial_report.py"), "--manifest", str(MANIFEST), "--roi", str(ROI), "--json"],
            [sys.executable, str(ROOT / "scripts/run_single_image_state_snapshot.py"), "--manifest", str(MANIFEST), "--roi", str(ROI), "--json"],
        ]
        forbidden = ("Authorization", "Bearer", "sk-", "data:image", '"raw_response"', str(ROOT))
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0)
            for term in forbidden:
                self.assertNotIn(term, result.stdout)


if __name__ == "__main__":
    unittest.main()
