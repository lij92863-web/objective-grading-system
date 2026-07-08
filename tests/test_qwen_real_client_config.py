import os
import unittest

from app.recognition.qwen_adapter import (
    QwenAdapterError,
    QwenAdapterErrorCode,
    QwenRequest,
    RealQwenClient,
)


class RealClientConfigTests(unittest.TestCase):
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

    def _request(self):
        from app.recognition.qwen_adapter.models import QwenImageInput
        img = QwenImageInput(
            image_id="test",
            image_base64="data:image/jpeg;base64,/9j/4AAQ",  # fake
        )
        return QwenRequest(prompt_type="choice_cell", prompt="", image=img)

    def test_disabled_when_env_not_set(self):
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request())
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.API_DISABLED)

    def test_disabled_when_enabled_is_false(self):
        os.environ["QWEN_API_ENABLED"] = "false"
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request())
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.API_DISABLED)

    def test_missing_api_key(self):
        os.environ["QWEN_API_ENABLED"] = "true"
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request())
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.MISSING_API_KEY)

    def test_missing_api_base(self):
        os.environ["QWEN_API_ENABLED"] = "true"
        os.environ["QWEN_API_KEY"] = "sk-test"
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request())
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.MISSING_API_BASE)

    def test_missing_model(self):
        os.environ["QWEN_API_ENABLED"] = "true"
        os.environ["QWEN_API_KEY"] = "sk-test"
        os.environ["QWEN_API_BASE"] = "https://api.example.com"
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request())
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.MISSING_MODEL)

    def test_does_not_read_dotenv(self):
        # We verify that no .env file is read by checking that
        # only explicit os.environ items are consulted.
        for key in list(os.environ):
            if key.startswith("QWEN_"):
                del os.environ[key]
        client = RealQwenClient()
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request())
        # Should be API_DISABLED, not some error from a .env parser
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.API_DISABLED)

    def test_explicit_disabled_override(self):
        os.environ["QWEN_API_ENABLED"] = "true"
        os.environ["QWEN_API_KEY"] = "sk-test"
        os.environ["QWEN_API_BASE"] = "https://api.example.com"
        os.environ["QWEN_MODEL"] = "qwen-vl-plus"
        client = RealQwenClient(enabled=False)
        with self.assertRaises(QwenAdapterError) as ctx:
            client.recognize_choice_cell(self._request())
        self.assertEqual(ctx.exception.code, QwenAdapterErrorCode.API_DISABLED)


if __name__ == "__main__":
    unittest.main()
