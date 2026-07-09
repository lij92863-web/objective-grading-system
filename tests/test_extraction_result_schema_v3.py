from __future__ import annotations

import unittest

from app.answer_extraction.extraction_result_schema import REQUIRED_RESULT_FIELDS, with_schema_defaults


class ExtractionResultSchemaV3Tests(unittest.TestCase):
    def test_all_required_fields_present_in_set(self):
        expected = {
            "schema_version", "run_id", "strategy", "status",
            "question_count", "answer_count", "accepted_count",
            "review_count", "blocked_count", "answers",
            "review_items", "blocking_errors", "warnings", "diagnostics",
        }
        self.assertEqual(REQUIRED_RESULT_FIELDS, expected)

    def test_defaults_fill_missing_keys(self):
        result = with_schema_defaults({"run_id": "x", "strategy": "same_file_boxed", "status": "accepted"})
        self.assertEqual(result["schema_version"], "answer_extraction.v3")
        self.assertEqual(result["warnings"], [])
        self.assertIn("diagnostics", result)

    def test_defaults_preserve_existing(self):
        result = with_schema_defaults({"run_id": "x", "strategy": "s", "status": "ok", "warnings": ["w1"]})
        self.assertEqual(result["warnings"], ["w1"])

    def test_blocked_count_from_blocking_errors(self):
        result = with_schema_defaults({"run_id": "x", "strategy": "s", "status": "blocked", "blocking_errors": ["e1", "e2"]})
        self.assertEqual(result["blocked_count"], 2)

    def test_empty_result_still_has_required_fields(self):
        result = with_schema_defaults({})
        essential_always_filled = {"schema_version", "blocked_count", "warnings", "diagnostics"}
        for field in essential_always_filled:
            self.assertIn(field, result, f"Missing essential field: {field}")

    def test_schema_version_is_v3(self):
        result = with_schema_defaults({})
        self.assertEqual(result["schema_version"], "answer_extraction.v3")


if __name__ == "__main__":
    unittest.main()
