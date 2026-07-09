"""R30: Qwen guard acceptance tests."""
import json, os, subprocess, sys, unittest
from pathlib import Path
from app.recognition.qwen_adapter.controlled_run_config import ControlledQwenRunConfig
from app.recognition.qwen_adapter.controlled_client import ControlledQwenClient, FakeQwenClient
from app.recognition.qwen_adapter.sanitizer import sanitize_qwen_output, sanitize_to_json
from app.recognition.qwen_adapter.response_parser import parse_qwen_response

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class QwenGuardAcceptanceTests(unittest.TestCase):
    def test_config_default_disabled(self):
        c = ControlledQwenRunConfig()
        self.assertFalse(c.allow_real_api)
        self.assertFalse(c.save_raw_response)
        self.assertFalse(c.emit_base64)

    def test_config_no_allow_real_api_blocks(self):
        c = ControlledQwenRunConfig()
        self.assertFalse(c.can_run())

    def test_config_no_image_blocks(self):
        c = ControlledQwenRunConfig(allow_real_api=True)
        self.assertFalse(c.can_run())

    def test_config_no_api_key_env_blocks(self):
        c = ControlledQwenRunConfig(allow_real_api=True, image_path="test.jpg")
        self.assertFalse(c.can_run())

    def test_save_raw_response_blocked(self):
        c = ControlledQwenRunConfig(allow_real_api=True, image_path="t.jpg", api_key_env="K",
                                     save_raw_response=True)
        self.assertFalse(c.can_run())

    def test_controlled_client_default_disabled(self):
        client = ControlledQwenClient()
        result = client.run()
        self.assertEqual(result.status, "disabled")

    def test_fake_client_available(self):
        client = FakeQwenClient()
        result = client.run()
        self.assertEqual(result.status, "ok")

    def test_sanitizer_removes_api_key(self):
        dirty = {"answer": "A", "api_key": "sk-secret1234", "Authorization": "Bearer tok"}
        clean = sanitize_qwen_output(dirty)
        self.assertNotIn("api_key", clean)
        self.assertNotIn("Authorization", clean)

    def test_sanitizer_removes_base64(self):
        clean = sanitize_qwen_output({"data": "data:image/png;base64,iVBOR..."})
        self.assertEqual(clean["data"], "[REDACTED]")

    def test_parser_handles_choice_response(self):
        from app.recognition.qwen_adapter.response_parser import parse_choice_response
        c = parse_choice_response({"answer": "A", "confidence": 0.95}, 1)
        self.assertEqual(c.value, "A")
        self.assertEqual(c.engine, "qwen")

    def test_parser_handles_malformed(self):
        result = parse_qwen_response("not a dict")
        self.assertEqual(result.status, "engine_error")

    def test_cli_fail_closed(self):
        r = subprocess.run([sys.executable, str(PROJECT_ROOT/"scripts/run_controlled_qwen_sample.py")],
                           capture_output=True, text=True, timeout=10)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("disabled", r.stdout.lower())

    def test_no_env_read(self):
        old = os.environ.pop("QWEN_API_KEY", None)
        try:
            c = ControlledQwenClient()
            result = c.run()
            self.assertEqual(result.status, "disabled")
        finally:
            if old: os.environ["QWEN_API_KEY"] = old


if __name__ == "__main__": unittest.main()
