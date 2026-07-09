"""Mutation tests for fake Qwen response handling — R381."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.single_sanitizer import sanitize_single_qwen_response
from app.recognition.qwen_adapter.single_response_parser import parse_single_qwen_response
from app.recognition.manual_roi_schema import load_manual_roi_file


class FakeResponseMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roi = load_manual_roi_file(
            "tests/fixtures/recognition/single_image/demo_manual_roi.json")
        fixture_path = Path("tests/fixtures/recognition/qwen_single_response/"
                           "fake_single_qwen_valid_choice_blank_identity.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            cls.base_payload = json.load(f)

    def _mutate_and_parse(self, payload):
        sanitized = sanitize_single_qwen_response(payload, request_id="mut-test")
        return parse_single_qwen_response(sanitized, self.roi)

    def test_mutate_option_to_z(self):
        payload = json.loads(json.dumps(self.base_payload))
        payload["items"][0]["answer"] = "Z"
        payload["items"][0]["invalid_option"] = True
        result = self._mutate_and_parse(payload)
        codes = result["parser_exception_codes"]
        self.assertTrue(any("INVALID_OPTION" in c for c in codes))

    def test_remove_question_id(self):
        payload = json.loads(json.dumps(self.base_payload))
        del payload["items"][0]["question_id"]
        result = self._mutate_and_parse(payload)
        codes = result["parser_exception_codes"]
        self.assertTrue(any("MISSING_QUESTION_ID" in c for c in codes))

    def test_add_unexpected_question_id(self):
        payload = json.loads(json.dumps(self.base_payload))
        payload["items"].append({
            "question_id": "Q999",
            "question_type": "single_choice",
            "answer": "A",
            "confidence": 0.9,
            "needs_review": False,
            "invalid_option": False,
            "warnings": [],
        })
        result = self._mutate_and_parse(payload)
        codes = result["parser_exception_codes"]
        self.assertTrue(any("UNEXPECTED_QUESTION_ID" in c for c in codes))

    def test_lower_confidence(self):
        payload = json.loads(json.dumps(self.base_payload))
        payload["items"][0]["confidence"] = 0.55
        result = self._mutate_and_parse(payload)
        parsed = result["parsed_candidates"]
        if parsed:
            self.assertTrue(parsed[0].get("needs_review", False))

    def test_invalid_choice_for_choice_question(self):
        payload = json.loads(json.dumps(self.base_payload))
        payload["items"][0]["answer"] = "E"
        result = self._mutate_and_parse(payload)
        codes = result["parser_exception_codes"]
        self.assertTrue(any("INVALID_OPTION" in c for c in codes))

    def test_empty_items_list(self):
        payload = {"items": []}
        result = self._mutate_and_parse(payload)
        self.assertEqual(len(result["parsed_candidates"]), 0)

    def test_items_not_list(self):
        payload = {"items": "not_a_list"}
        result = self._mutate_and_parse(payload)
        self.assertIn("ENGINE_NOT_OK", result["parser_exception_codes"])

    def test_identity_not_auto_confirmed(self):
        payload = json.loads(json.dumps(self.base_payload))
        result = self._mutate_and_parse(payload)
        identity = result.get("identity_result")
        if identity:
            self.assertTrue(identity.get("needs_review", False))
            self.assertFalse(identity.get("confirmed", True))


if __name__ == "__main__":
    unittest.main()
