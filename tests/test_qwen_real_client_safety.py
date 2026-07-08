import os
import tempfile
import unittest
from pathlib import Path

from app.recognition.qwen_adapter import (
    QwenAdapterError,
    QwenAdapterErrorCode,
    QwenRequest,
    RealQwenClient,
)


class RealClientSafetyTests(unittest.TestCase):
    def setUp(self):
        self._saved = {}
        for key in (
            "QWEN_API_ENABLED",
            "QWEN_API_KEY",
            "QWEN_API_BASE",
            "QWEN_MODEL",
        ):
            self._saved[key] = os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self._saved.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def _request_with_path(self, image_path: str):
        from app.recognition.qwen_adapter.models import QwenImageInput
        img = QwenImageInput(
            image_id="test",
            image_path=image_path,
        )
        return QwenRequest(prompt_type="choice_cell", prompt="", image=img)

    def _request_with_base64(self):
        from app.recognition.qwen_adapter.models import QwenImageInput
        img = QwenImageInput(
            image_id="test",
            image_base64="data:image/jpeg;base64,ZmFrZQ==",
        )
        return QwenRequest(prompt_type="choice_cell", prompt="", image=img)

    # -- image not found ----------------------------------------------------

    def test_image_not_found(self):
        req = self._request_with_path("/nonexistent/path/img.png")
        # The client first checks is_enabled, so we need full config
        os.environ["QWEN_API_ENABLED"] = "true"
        os.environ["QWEN_API_KEY"] = "sk-test"
        os.environ["QWEN_API_BASE"] = "https://api.example.com"
        os.environ["QWEN_MODEL"] = "qwen-vl-plus"
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(req)
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.IMAGE_NOT_FOUND)

    def test_no_image_in_request(self):
        os.environ["QWEN_API_ENABLED"] = "true"
        os.environ["QWEN_API_KEY"] = "sk-test"
        os.environ["QWEN_API_BASE"] = "https://api.example.com"
        os.environ["QWEN_MODEL"] = "qwen-vl-plus"
        req = QwenRequest(prompt_type="choice_cell", prompt="")
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(req)
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.IMAGE_NOT_FOUND)

    # -- base64 safety ------------------------------------------------------

    def test_does_not_log_base64_in_error(self):
        from app.recognition.qwen_adapter.real_client import _safe_image_ref
        req = self._request_with_base64()
        ref = _safe_image_ref(req)
        self.assertIn("<base64 omitted>", ref)
        self.assertNotIn("ZmFrZQ", ref)

    def test_error_message_no_api_key_leak(self):
        os.environ["QWEN_API_ENABLED"] = "true"
        os.environ["QWEN_API_KEY"] = "sk-super-secret-key-12345"
        os.environ["QWEN_API_BASE"] = "https://api.example.com"
        os.environ["QWEN_MODEL"] = "qwen-vl-plus"
        req = self._request_with_path("/nonexistent/path/img.png")
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(req)
        msg = str(ctx.exception.message)
        self.assertNotIn("sk-super-secret-key-12345", msg)
        self.assertNotIn("super-secret", msg)

    def test_api_disabled_message_has_no_sensitive_data(self):
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request_with_base64())
        msg = str(ctx.exception.message)
        self.assertIn("QWEN_API_ENABLED", msg)


if __name__ == "__main__":
    unittest.main()
