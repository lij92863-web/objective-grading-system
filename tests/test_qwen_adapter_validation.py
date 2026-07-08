import unittest

from app.recognition.qwen_adapter import (
    QwenAdapterErrorCode,
    validate_blank_answer_response,
    validate_choice_cell_response,
    validate_complex_blank_judgment_response,
    validate_name_field_response,
)


class NameFieldValidationTests(unittest.TestCase):
    def test_empty_raw_text_invalid(self):
        errors = validate_name_field_response(
            {"raw_text": "", "confidence": 0.9}
        )
        self.assertIn(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD, errors)

    def test_valid_confidence(self):
        errors = validate_name_field_response(
            {"raw_text": "1李明", "confidence": 0.95}
        )
        self.assertEqual(errors, [])

    def test_missing_raw_text_key(self):
        errors = validate_name_field_response({"confidence": 0.9})
        self.assertIn(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD, errors)


class ChoiceCellValidationTests(unittest.TestCase):
    def test_ab_legal(self):
        errors = validate_choice_cell_response(
            {"answer": "AB", "confidence": 0.96}
        )
        self.assertEqual(errors, [])

    def test_single_legal(self):
        errors = validate_choice_cell_response(
            {"answer": "C", "confidence": 0.90}
        )
        self.assertEqual(errors, [])

    def test_e_illegal(self):
        errors = validate_choice_cell_response(
            {"answer": "E", "confidence": 0.80}
        )
        self.assertIn(QwenAdapterErrorCode.INVALID_VERDICT, errors)

    def test_blank_legal(self):
        errors = validate_choice_cell_response(
            {"answer": "BLANK", "confidence": 0.99}
        )
        self.assertEqual(errors, [])

    def test_unclear_legal(self):
        errors = validate_choice_cell_response(
            {"answer": "UNCLEAR", "confidence": 0.50}
        )
        self.assertEqual(errors, [])

    def test_lowercase_handled(self):
        # validator normalises to upper — 'ab' -> 'AB' -> valid
        data = {"answer": "ab", "confidence": 0.96}
        # The _check_confidence part validates numeric confidence
        errors = validate_choice_cell_response(data)
        self.assertEqual(errors, [])


class BlankAnswerValidationTests(unittest.TestCase):
    def test_recognized_legal(self):
        errors = validate_blank_answer_response(
            {
                "raw_text": "x+1",
                "confidence": 0.92,
                "status": "recognized",
            }
        )
        self.assertEqual(errors, [])

    def test_blank_legal(self):
        errors = validate_blank_answer_response(
            {"status": "blank", "confidence": 0.99}
        )
        self.assertEqual(errors, [])

    def test_unclear_legal(self):
        errors = validate_blank_answer_response(
            {"status": "unclear", "confidence": 0.40}
        )
        self.assertEqual(errors, [])

    def test_invalid_status_errors(self):
        errors = validate_blank_answer_response(
            {
                "raw_text": "x",
                "status": "unknown_status",
                "confidence": 0.90,
            }
        )
        self.assertIn(QwenAdapterErrorCode.INVALID_VERDICT, errors)

    def test_missing_raw_and_status(self):
        errors = validate_blank_answer_response({"confidence": 0.90})
        self.assertIn(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD, errors)


class ComplexJudgmentValidationTests(unittest.TestCase):
    def test_correct_high_conf_with_reason_valid(self):
        errors = validate_complex_blank_judgment_response(
            {
                "verdict": "correct",
                "confidence": 0.96,
                "reason": "equivalent",
                "normalized_standard": "x > 1",
                "normalized_student": "x > 1",
                "requires_review": False,
            }
        )
        self.assertEqual(errors, [])

    def test_correct_missing_normalized_invalid(self):
        errors = validate_complex_blank_judgment_response(
            {
                "verdict": "correct",
                "confidence": 0.96,
                "reason": "equivalent",
            }
        )
        self.assertIn(QwenAdapterErrorCode.MISSING_REQUIRED_FIELD, errors)

    def test_needs_review_valid(self):
        errors = validate_complex_blank_judgment_response(
            {
                "verdict": "needs_review",
                "confidence": 0.80,
                "reason": "uncertain",
            }
        )
        self.assertEqual(errors, [])

    def test_confidence_above_1_invalid(self):
        errors = validate_complex_blank_judgment_response(
            {
                "verdict": "correct",
                "confidence": 1.2,
                "reason": "ok",
                "normalized_standard": "x",
                "normalized_student": "x",
            }
        )
        self.assertIn(QwenAdapterErrorCode.INVALID_CONFIDENCE, errors)

    def test_requires_review_not_bool(self):
        errors = validate_complex_blank_judgment_response(
            {
                "verdict": "correct",
                "confidence": 0.96,
                "reason": "ok",
                "normalized_standard": "x",
                "normalized_student": "x",
                "requires_review": "yes",
            }
        )
        self.assertIn(QwenAdapterErrorCode.INVALID_VERDICT, errors)

    def test_wrong_verdict_valid(self):
        errors = validate_complex_blank_judgment_response(
            {
                "verdict": "wrong",
                "confidence": 0.95,
                "reason": "not same",
                "normalized_standard": "x=2",
                "normalized_student": "x=3",
                "requires_review": False,
            }
        )
        self.assertEqual(errors, [])

    def test_partial_verdict_valid(self):
        errors = validate_complex_blank_judgment_response(
            {
                "verdict": "partial",
                "confidence": 0.95,
                "reason": "incomplete",
                "normalized_standard": "(x+1)(x-1)",
                "normalized_student": "x^2-1",
                "requires_review": False,
            }
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
