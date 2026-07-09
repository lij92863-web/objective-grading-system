"""Tests for single Qwen response parser v2 — R370."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.single_sanitized_output import (
    SingleQwenSanitizedOutput,
    SanitizedCandidate,
    SanitizedIdentityCandidate,
)
from app.recognition.qwen_adapter.single_response_parser import parse_single_qwen_response
from app.recognition.manual_roi_schema import load_manual_roi_file


class SingleQwenResponseParserV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roi = load_manual_roi_file(
            "tests/fixtures/recognition/single_image/demo_manual_roi.json")

    def _make_sanitized(self, candidates, identity=None, engine_status="ok"):
        return SingleQwenSanitizedOutput(
            request_id="test",
            engine_status=engine_status,
            candidates=candidates,
            candidate_count=len(candidates),
            identity_candidate=identity,
        )

    def test_valid_choice_accepted(self):
        candidates = [
            SanitizedCandidate(question_id="Q1", answer="A", confidence=0.95,
                             question_type="single_choice")
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        self.assertEqual(len(result["parsed_candidates"]), 1)
        codes = result["parser_exception_codes"]
        self.assertFalse(any("INVALID_OPTION" in c for c in codes))

    def test_invalid_option_produces_exception(self):
        candidates = [
            SanitizedCandidate(question_id="Q1", answer="Z", confidence=0.85,
                             invalid_option=True)
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        codes = result["parser_exception_codes"]
        self.assertTrue(any("INVALID_OPTION" in c for c in codes))

    def test_invalid_non_abcd_choice(self):
        candidates = [
            SanitizedCandidate(question_id="Q1", answer="E", confidence=0.80,
                             question_type="single_choice")
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        codes = result["parser_exception_codes"]
        self.assertTrue(any("INVALID_OPTION" in c for c in codes))

    def test_missing_question_id(self):
        candidates = [
            SanitizedCandidate(question_id="", answer="A", confidence=0.90)
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        self.assertTrue(any("MISSING_QUESTION_ID" in c for c in result["parser_exception_codes"]))

    def test_unexpected_question_id(self):
        candidates = [
            SanitizedCandidate(question_id="Q99", answer="A", confidence=0.90)
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        self.assertTrue(any("UNEXPECTED" in c for c in result["parser_exception_codes"]))

    def test_blank_low_confidence(self):
        candidates = [
            SanitizedCandidate(question_id="Q6", answer="sqrt(2)", confidence=0.55,
                             question_type="blank")
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        parsed = result["parsed_candidates"]
        if parsed:
            self.assertTrue(parsed[0].get("needs_review", False))

    def test_identity_candidate_not_confirmed(self):
        candidates = []
        identity = SanitizedIdentityCandidate(
            raw_text="S001Test", student_number="S001", student_name="Test")
        sanitized = self._make_sanitized(candidates, identity=identity)
        result = parse_single_qwen_response(sanitized, self.roi)
        id_result = result.get("identity_result")
        if id_result:
            self.assertTrue(id_result["needs_review"])
            self.assertFalse(id_result["confirmed"])

    def test_parser_does_not_call_grade_all(self):
        candidates = [SanitizedCandidate(question_id="Q1", answer="A", confidence=0.95)]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        self.assertNotIn("score", result)
        self.assertNotIn("grade", result)

    def test_parser_does_not_create_confirmed_submission(self):
        candidates = [SanitizedCandidate(question_id="Q1", answer="A", confidence=0.95)]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        for c in result.get("parsed_candidates", []):
            self.assertNotIn("confirmed", c)
            self.assertNotIn("submission", c)

    def test_engine_error_handled(self):
        candidates = []
        sanitized = SingleQwenSanitizedOutput(
            request_id="test", engine_status="engine_error",
            exception_codes=["MALFORMED_RESPONSE"])
        result = parse_single_qwen_response(sanitized, self.roi)
        self.assertIn("ENGINE_NOT_OK", result["parser_exception_codes"])

    def test_multiple_invalid_options(self):
        candidates = [
            SanitizedCandidate(question_id="Q1", answer="Z", confidence=0.80, invalid_option=True),
            SanitizedCandidate(question_id="Q2", answer="E", confidence=0.80),
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        codes = result["parser_exception_codes"]
        invalid_count = sum(1 for c in codes if "INVALID_OPTION" in c)
        self.assertGreaterEqual(invalid_count, 1)

    def test_missing_expected_question_ids_warning(self):
        candidates = [
            SanitizedCandidate(question_id="Q1", answer="A", confidence=0.95)
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        self.assertTrue(
            any("MISSING_EXPECTED" in w for w in result["parser_warnings"]))

    def test_deduplicate_question_ids(self):
        candidates = [
            SanitizedCandidate(question_id="Q1", answer="A", confidence=0.90),
            SanitizedCandidate(question_id="Q1", answer="B", confidence=0.80),
        ]
        sanitized = self._make_sanitized(candidates)
        result = parse_single_qwen_response(sanitized, self.roi)
        # Both should be parsed, parser does not deduplicate
        self.assertEqual(len(result["parsed_candidates"]), 2)


if __name__ == "__main__":
    unittest.main()
