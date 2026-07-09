"""R40: Secret leak guard — no API keys, base64, raw responses in output."""
import json, unittest
from app.recognition.qwen_adapter.sanitizer import sanitize_qwen_output


class RecognitionSecretLeakGuardTests(unittest.TestCase):
    def test_sk_key_removed(self):
        clean = sanitize_qwen_output({"result": "ok", "api_key": "sk-abc123def456"})
        self.assertNotIn("sk-abc", json.dumps(clean))

    def test_authorization_removed(self):
        clean = sanitize_qwen_output({"Authorization": "Bearer xyz"})
        self.assertNotIn("Authorization", clean)

    def test_bearer_removed(self):
        clean = sanitize_qwen_output({"headers": "Bearer token123"})
        self.assertIn("[REDACTED]", str(clean))

    def test_base64_marker_removed(self):
        clean = sanitize_qwen_output({"img": "data:image/png;base64,iVBORw0KGgo="})
        self.assertIn("[REDACTED]", str(clean))

    def test_raw_response_removed(self):
        clean = sanitize_qwen_output({"raw_response": "secret", "data": "ok"})
        self.assertNotIn("raw_response", clean)

    def test_full_path_redacted(self):
        clean = sanitize_qwen_output({"path": "C:/Users/test/image.jpg"}, "C:/Users/test/image.jpg")
        self.assertNotIn("C:/Users", str(clean))


if __name__ == "__main__": unittest.main()
