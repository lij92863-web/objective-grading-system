"""Tests for single Qwen sanitizer — R369."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.single_sanitizer import sanitize_single_qwen_response


class SingleQwenSanitizerTests(unittest.TestCase):
    def test_valid_response_sanitized(self):
        payload = {
            "items": [
                {"question_id": "Q1", "question_type": "single_choice",
                 "answer": "A", "confidence": 0.95}
            ]
        }
        result = sanitize_single_qwen_response(payload, request_id="test")
        self.assertEqual(result.engine_status, "ok")
        self.assertEqual(result.candidate_count, 1)
        self.assertFalse(result.real_api_called)

    def test_strips_api_key(self):
        payload = {
            "api_key": "sk-secret-value",
            "items": [{"question_id": "Q1", "answer": "A", "confidence": 0.95}],
        }
        result = sanitize_single_qwen_response(payload)
        self.assertGreater(len(result.warnings), 0)
        self.assertTrue(any("API" in w or "STRIPPED" in w for w in result.warnings))

    def test_strips_authorization(self):
        payload = {
            "authorization": "Bearer sk-secret",
            "items": [{"question_id": "Q1", "answer": "A", "confidence": 0.95}],
        }
        result = sanitize_single_qwen_response(payload)
        self.assertGreater(len(result.warnings), 0)

    def test_strips_base64(self):
        payload = {
            "data:image": "data:image/png;base64,iVBORw0KGgo...",
            "items": [],
        }
        result = sanitize_single_qwen_response(payload)
        self.assertGreater(len(result.warnings), 0)

    def test_strips_raw_image_data(self):
        payload = {
            "base64": "longbase64string...",
            "items": [],
        }
        result = sanitize_single_qwen_response(payload)
        self.assertGreater(len(result.warnings), 0)

    def test_identity_preserved(self):
        payload = {
            "items": [{"question_id": "Q1", "answer": "A", "confidence": 0.95}],
            "identity_candidate": {
                "raw_text": "S001Test", "student_number": "S001",
                "student_name": "Test", "confidence": 0.88,
            },
        }
        result = sanitize_single_qwen_response(payload)
        self.assertIsNotNone(result.identity_candidate)
        self.assertTrue(result.identity_candidate.needs_review)

    def test_malformed_items_not_list(self):
        payload = {"items": "not a list"}
        result = sanitize_single_qwen_response(payload)
        self.assertEqual(result.engine_status, "engine_error")
        self.assertIn("MALFORMED_ITEMS_NOT_LIST", result.exception_codes)

    def test_empty_response(self):
        payload = {}
        result = sanitize_single_qwen_response(payload)
        self.assertEqual(result.engine_status, "engine_error")
        self.assertIn("EMPTY_RESPONSE_AFTER_SANITIZATION", result.exception_codes)

    def test_confidence_clamped(self):
        payload = {
            "items": [{"question_id": "Q1", "answer": "A", "confidence": 1.5}]
        }
        result = sanitize_single_qwen_response(payload)
        self.assertEqual(result.candidates[0].confidence, 1.0)

    def test_negative_confidence_clamped(self):
        payload = {
            "items": [{"question_id": "Q1", "answer": "A", "confidence": -0.5}]
        }
        result = sanitize_single_qwen_response(payload)
        self.assertEqual(result.candidates[0].confidence, 0.0)

    def test_no_guess_answer_on_malformed(self):
        payload = {"items": [{"not_question_id": "X"}]}
        result = sanitize_single_qwen_response(payload)
        if result.candidates:
            self.assertEqual(result.candidates[0].question_id, "")

    def test_multiple_candidates(self):
        payload = {
            "items": [
                {"question_id": "Q1", "answer": "A", "confidence": 0.9},
                {"question_id": "Q2", "answer": "B", "confidence": 0.8},
                {"question_id": "Q3", "answer": "C", "confidence": 0.7},
            ]
        }
        result = sanitize_single_qwen_response(payload)
        self.assertEqual(result.candidate_count, 3)
        self.assertEqual(len(result.candidates), 3)


if __name__ == "__main__":
    unittest.main()
