"""Tests for SingleQwenSanitizedOutput — R368."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.single_sanitized_output import (
    SingleQwenSanitizedOutput,
    SanitizedCandidate,
    SanitizedIdentityCandidate,
    validate_sanitized_output,
)


class SingleQwenSanitizedOutputTests(unittest.TestCase):
    def test_default_raw_response_saved_false(self):
        s = SingleQwenSanitizedOutput()
        self.assertFalse(s.raw_response_saved)

    def test_default_base64_emitted_false(self):
        s = SingleQwenSanitizedOutput()
        self.assertFalse(s.base64_emitted)

    def test_default_real_api_called_false(self):
        s = SingleQwenSanitizedOutput()
        self.assertFalse(s.real_api_called)

    def test_no_api_key_in_output(self):
        s = SingleQwenSanitizedOutput(request_id="test-123")
        d = s.to_dict()
        raw = json.dumps(d)
        self.assertNotIn("sk-", raw)
        self.assertNotIn("Bearer ", raw)

    def test_no_base64_in_output(self):
        s = SingleQwenSanitizedOutput()
        d = s.to_dict()
        raw = json.dumps(d)
        self.assertNotIn("data:image", raw)

    def test_no_raw_response_in_output(self):
        s = SingleQwenSanitizedOutput()
        d = s.to_dict()
        self.assertNotIn("raw_http_response", json.dumps(d).lower())

    def test_candidates_serializable(self):
        candidate = SanitizedCandidate(
            question_id="Q1", answer="A", confidence=0.95)
        s = SingleQwenSanitizedOutput(
            candidates=[candidate], candidate_count=1)
        d = s.to_dict()
        self.assertEqual(d["candidate_count"], 1)
        self.assertEqual(len(d["candidates"]), 1)
        self.assertEqual(d["candidates"][0]["question_id"], "Q1")

    def test_validate_blocks_raw_response_saved(self):
        s = SingleQwenSanitizedOutput(raw_response_saved=True)
        result = validate_sanitized_output(s)
        self.assertFalse(result["valid"])
        self.assertIn("RAW_RESPONSE_SAVED_MUST_BE_FALSE", result["blockers"])

    def test_validate_blocks_base64_emitted(self):
        s = SingleQwenSanitizedOutput(base64_emitted=True)
        result = validate_sanitized_output(s)
        self.assertFalse(result["valid"])
        self.assertIn("BASE64_EMITTED_MUST_BE_FALSE", result["blockers"])

    def test_json_round_trip(self):
        s = SingleQwenSanitizedOutput(
            request_id="req-1",
            candidates=[SanitizedCandidate(question_id="Q1", answer="A")],
            candidate_count=1,
        )
        d = s.to_dict()
        raw = json.dumps(d)
        parsed = json.loads(raw)
        self.assertEqual(parsed["request_id"], "req-1")
        self.assertEqual(parsed["candidate_count"], 1)

    def test_identity_candidate_serializable(self):
        identity = SanitizedIdentityCandidate(
            raw_text="1测试", student_number="1", student_name="测试")
        s = SingleQwenSanitizedOutput(identity_candidate=identity)
        d = s.to_dict()
        self.assertIsNotNone(d["identity_candidate"])
        self.assertEqual(d["identity_candidate"]["student_name"], "测试")


if __name__ == "__main__":
    unittest.main()
