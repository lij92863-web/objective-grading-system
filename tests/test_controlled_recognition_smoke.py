"""R18: Controlled recognition smoke test."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "run_controlled_recognition_fixture.py"
IMAGE = PROJECT_ROOT / "tests/fixtures/recognition/images/fake_answer_sheet.jpg"
LAYOUT = PROJECT_ROOT / "tests/fixtures/recognition/layouts/demo_layout.json"
PAYLOADS = PROJECT_ROOT / "tests/fixtures/recognition/fake_engine_payloads"


class ControlledRecognitionSmokeTests(unittest.TestCase):
    def test_fixture_script_success(self):
        t = tempfile.mkdtemp(prefix="r18_", dir=PROJECT_ROOT/"data")
        try:
            r = subprocess.run([sys.executable, str(SCRIPT), "--image", str(IMAGE),
                "--layout", str(LAYOUT), "--payload-dir", str(PAYLOADS),
                "--out-dir", str(Path(t)/"out"), "--dry-run"],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0, f"Script failed: {r.stderr}")
            out = Path(t)/"out"
            for f in ["recognition_run.json","recognition_draft.json","exception_queue.json","recognition_summary.json"]:
                self.assertTrue((out/f).exists(), f"Missing {f}")
            summary = json.loads((out/"recognition_summary.json").read_text("utf-8"))
            self.assertIn("auto_accepted", summary)
            self.assertIn("needs_review", summary)
            self.assertIn("blocking", summary)
        finally:
            import shutil; shutil.rmtree(t, ignore_errors=True)

    def test_no_real_api_called(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--image", str(IMAGE),
            "--layout", str(LAYOUT), "--payload-dir", str(PAYLOADS),
            "--out-dir", str(PROJECT_ROOT/"data/tmp/r18_smoke"), "--dry-run"],
            capture_output=True, text=True, timeout=30)
        self.assertNotIn("QWEN_API", result.stdout + result.stderr)
        self.assertNotIn("base64", result.stdout.lower() + result.stderr.lower())


if __name__ == "__main__": unittest.main()
