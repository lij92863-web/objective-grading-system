"""R13: Expanded exception queue tests."""
import json, unittest
from app.recognition.expanded_exceptions import (
    exception_level, has_blocking, summarize_queue, export_exception_json,
    EXCEPTION_LEVELS)


class RecognitionExpandedExceptionTests(unittest.TestCase):
    def test_blocking_codes(self):
        for code in ["IMAGE_MISSING","IDENTITY_CONFLICT","INVALID_OPTION","ENGINE_ERROR","API_DISABLED","BLOCKING_BEFORE_GRADING"]:
            self.assertEqual("blocking", exception_level(code))

    def test_review_codes(self):
        for code in ["CHOICE_CONFLICT","CHOICE_LOW_CONFIDENCE","BLANK_LOW_CONFIDENCE","CONFIRMATION_REQUIRED"]:
            self.assertEqual("review", exception_level(code))

    def test_has_blocking(self):
        self.assertTrue(has_blocking(["IDENTITY_CONFLICT", "CHOICE_LOW_CONFIDENCE"]))
        self.assertFalse(has_blocking(["CHOICE_LOW_CONFIDENCE"]))

    def test_summarize_queue(self):
        s = summarize_queue(["IDENTITY_CONFLICT", "CHOICE_CONFLICT", "CHOICE_LOW_CONFIDENCE"])
        self.assertEqual(s["total"], 3)
        self.assertEqual(s["by_level"]["blocking"], 1)
        self.assertTrue(s["has_blocking"])

    def test_export_no_sensitive_data(self):
        result = export_exception_json(["IMAGE_MISSING"])
        text = json.dumps(result)
        self.assertNotIn("base64", text.lower())
        self.assertNotIn("api_key", text.lower())

    def test_blocking_prevents_confirmation(self):
        self.assertTrue(has_blocking(["IDENTITY_CONFLICT"]))

    def test_needs_review_does_not_auto_confirm(self):
        self.assertFalse(has_blocking(["CHOICE_LOW_CONFIDENCE"]))


if __name__ == "__main__": unittest.main()
