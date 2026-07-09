"""Tests for parser candidate audit — R371."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.parser_candidate_audit import (
    ParserCandidateAudit,
    audit_parser_candidates,
)
from app.recognition.qwen_adapter.single_sanitized_output import SingleQwenSanitizedOutput


class ParserCandidateAuditTests(unittest.TestCase):
    def test_ready_for_grading_always_false(self):
        audit = ParserCandidateAudit()
        self.assertFalse(audit.ready_for_grading)

    def test_ready_for_review_queue_when_no_blockers(self):
        sanitized = SingleQwenSanitizedOutput(engine_status="ok")
        parsed = {
            "parsed_candidates": [
                {"question_id": "Q1", "needs_review": False}
            ],
            "parser_exception_codes": [],
            "parser_warnings": [],
        }
        audit = audit_parser_candidates(parsed, sanitized, "req-1")
        self.assertTrue(audit.ready_for_review_queue)
        self.assertFalse(audit.ready_for_grading)

    def test_invalid_option_blocks_ready_for_review(self):
        sanitized = SingleQwenSanitizedOutput(engine_status="ok")
        parsed = {
            "parsed_candidates": [
                {"question_id": "Q1", "needs_review": True}
            ],
            "parser_exception_codes": ["INVALID_OPTION:Q1"],
            "parser_warnings": [],
        }
        audit = audit_parser_candidates(parsed, sanitized, "req-1")
        self.assertFalse(audit.ready_for_review_queue)
        self.assertFalse(audit.ready_for_grading)
        self.assertEqual(audit.invalid_option_count, 1)

    def test_identity_candidate_blocks_ready_for_review(self):
        sanitized = SingleQwenSanitizedOutput(engine_status="ok")
        parsed = {
            "parsed_candidates": [
                {"question_id": "Q1", "needs_review": False}
            ],
            "parser_exception_codes": [],
            "parser_warnings": [],
            "identity_result": {"needs_review": True},
        }
        audit = audit_parser_candidates(parsed, sanitized, "req-1")
        self.assertFalse(audit.ready_for_review_queue)
        self.assertFalse(audit.ready_for_grading)

    def test_unexpected_question_id_blocks_ready_for_review(self):
        sanitized = SingleQwenSanitizedOutput(engine_status="ok")
        parsed = {
            "parsed_candidates": [
                {"question_id": "Q1", "needs_review": False}
            ],
            "parser_exception_codes": ["UNEXPECTED_QUESTION_ID:Q99"],
            "parser_warnings": [],
        }
        audit = audit_parser_candidates(parsed, sanitized, "req-1")
        self.assertFalse(audit.ready_for_review_queue)
        self.assertEqual(audit.unexpected_question_id_count, 1)

    def test_engine_error_blocks_ready_for_review(self):
        sanitized = SingleQwenSanitizedOutput(engine_status="engine_error")
        parsed = {
            "parsed_candidates": [
                {"question_id": "Q1", "needs_review": False}
            ],
            "parser_exception_codes": [],
            "parser_warnings": [],
        }
        audit = audit_parser_candidates(parsed, sanitized, "req-1")
        self.assertFalse(audit.ready_for_review_queue)
        self.assertFalse(audit.ready_for_grading)

    def test_count_fields_accurate(self):
        sanitized = SingleQwenSanitizedOutput(engine_status="ok")
        parsed = {
            "parsed_candidates": [
                {"question_id": "Q1", "needs_review": False},
                {"question_id": "Q2", "needs_review": True},
                {"question_id": "Q3", "needs_review": False},
            ],
            "parser_exception_codes": ["INVALID_OPTION:Q2"],
            "parser_warnings": [],
        }
        audit = audit_parser_candidates(parsed, sanitized, "req-1")
        self.assertEqual(audit.candidate_count, 3)
        self.assertEqual(audit.valid_candidate_count, 2)
        self.assertEqual(audit.review_candidate_count, 1)

    def test_no_api_key_in_audit(self):
        sanitized = SingleQwenSanitizedOutput(engine_status="ok")
        parsed = {"parsed_candidates": [], "parser_exception_codes": []}
        audit = audit_parser_candidates(parsed, sanitized, "req-1")
        d = audit.to_dict()
        import json
        raw = json.dumps(d)
        self.assertNotIn("sk-", raw)

    def test_to_dict_includes_all_fields(self):
        audit = ParserCandidateAudit(request_id="req-1", candidate_count=5,
                                     valid_candidate_count=3, review_candidate_count=2)
        d = audit.to_dict()
        self.assertEqual(d["request_id"], "req-1")
        self.assertEqual(d["candidate_count"], 5)
        self.assertFalse(d["ready_for_grading"])


if __name__ == "__main__":
    unittest.main()
