import json
import unittest

from app.recognition.qwen_adapter import (
    FakeQwenClient,
    QwenRequest,
    QwenRawResponse,
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
)


class FakeClientTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeQwenClient()

    # -- default responses -------------------------------------------------

    def test_name_field_default(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        self.assertIsInstance(resp, QwenRawResponse)
        self.assertIn("raw_text", resp.parsed_json)
        self.assertIn("confidence", resp.parsed_json)

    def test_choice_cell_default(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_CHOICE_CELL, prompt="test")
        resp = self.client.recognize_choice_cell(req)
        self.assertIn("answer", resp.parsed_json)
        self.assertEqual(resp.parsed_json["answer"], "AB")

    def test_blank_answer_default(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_BLANK_ANSWER, prompt="test")
        resp = self.client.recognize_blank_answer(req)
        self.assertEqual(resp.parsed_json["raw_text"], "1/2")
        self.assertIn("latex", resp.parsed_json)

    def test_complex_judgment_default(self):
        req = QwenRequest(
            prompt_type=PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT, prompt="test"
        )
        resp = self.client.judge_complex_blank(req)
        self.assertEqual(resp.parsed_json["verdict"], "correct")
        self.assertEqual(resp.parsed_json["confidence"], 0.96)

    # -- injected errors ---------------------------------------------------

    def test_inject_invalid_json(self):
        self.client.inject_error("invalid_json")
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        self.assertIsNone(resp.parsed_json)
        self.assertEqual(resp.raw_text.strip(), "{not json")

    def test_inject_missing_field(self):
        self.client.inject_error("missing_field")
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        self.assertIsNotNone(resp.parsed_json)
        # raw_text missing, only confidence present
        self.assertNotIn("raw_text", resp.parsed_json)

    def test_inject_custom_payload(self):
        custom = {"raw_text": "custom_value", "confidence": 0.99}
        self.client.inject_custom_payload(custom)
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        self.assertEqual(resp.parsed_json["raw_text"], "custom_value")

    def test_clear_injection_restores_default(self):
        self.client.inject_error("invalid_json")
        self.client.clear_injection()
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        self.assertIsNotNone(resp.parsed_json)
        self.assertIn("raw_text", resp.parsed_json)

    def test_request_id_is_set(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        self.assertTrue(len(req.request_id) > 0)

    def test_model_field_set(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        self.assertEqual(resp.model, "fake-qwen")


if __name__ == "__main__":
    unittest.main()
