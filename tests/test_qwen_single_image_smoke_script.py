import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "qwen_single_image_smoke.py"


class SmokeScriptTests(unittest.TestCase):
    def setUp(self):
        # Create a tiny fake image file
        self._tmpdir = tempfile.TemporaryDirectory()
        self._img = Path(self._tmpdir.name) / "test.png"
        # Minimal valid PNG bytes
        self._img.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    def tearDown(self):
        self._tmpdir.cleanup()

    def _run(self, *extra_args, env=None) -> subprocess.CompletedProcess:
        cmd = [
            sys.executable,
            str(SMOKE_SCRIPT),
            "--image",
            str(self._img),
            "--prompt-type",
            "choice_cell",
        ] + list(extra_args)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env or os.environ,
        )

    # -- dry-run (default) ---------------------------------------------------

    def test_dry_run_default(self):
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY-RUN", result.stdout)
        self.assertIn("request was NOT sent", result.stdout)

    def test_dry_run_has_request_id(self):
        result = self._run()
        self.assertIn("request_id", result.stdout)

    def test_dry_run_has_no_api_key(self):
        result = self._run()
        self.assertNotIn("QWEN_API_KEY=", result.stdout)

    def test_dry_run_has_no_base64(self):
        result = self._run()
        self.assertIn("<not loaded in dry-run>", result.stdout)

    # -- missing image -------------------------------------------------------

    def test_missing_image_errors(self):
        cmd = [
            sys.executable,
            str(SMOKE_SCRIPT),
            "--image",
            "/no/such/file.png",
            "--prompt-type",
            "choice_cell",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    # -- missing prompt_type ------------------------------------------------

    def test_missing_prompt_type_errors(self):
        cmd = [
            sys.executable,
            str(SMOKE_SCRIPT),
            "--image",
            str(self._img),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    # -- complex_blank_judgment requires extra args --------------------------

    def test_complex_blank_requires_answers(self):
        cmd = [
            sys.executable,
            str(SMOKE_SCRIPT),
            "--image",
            str(self._img),
            "--prompt-type",
            "complex_blank_judgment",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("standard-answer", result.stderr)

    def test_complex_blank_with_answers_dry_run(self):
        cmd = [
            sys.executable,
            str(SMOKE_SCRIPT),
            "--image",
            str(self._img),
            "--prompt-type",
            "complex_blank_judgment",
            "--standard-answer",
            "x>1",
            "--student-answer",
            "(1,+oo)",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    # -- check all prompt_types work in dry-run ------------------------------

    def test_name_field_dry_run(self):
        result = self._run("--prompt-type", "name_field")
        self.assertEqual(result.returncode, 0)

    def test_blank_answer_dry_run(self):
        result = self._run("--prompt-type", "blank_answer")
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
