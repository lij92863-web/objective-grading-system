import unittest

from app.recognition.choice_mock import normalize_choice_recognition
from app.recognition.models import ChoiceCellOutput, RecognizedAnswerDraft


class ChoiceMockTests(unittest.TestCase):
    def test_single_option_normal(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("A", 0.95), 1)
        self.assertEqual(draft.normalized_text, "A")
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_DRAFT)
        self.assertFalse(draft.needs_review)

    def test_multi_option_sorted(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("BA", 0.92), 2)
        self.assertEqual(draft.normalized_text, "AB")
        self.assertEqual(draft.question_type, "multiple_choice")

    def test_three_option(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("BCD", 0.88), 3)
        self.assertEqual(draft.normalized_text, "BCD")

    def test_blank(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("blank", 0.99), 4)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_BLANK)
        self.assertFalse(draft.needs_review)

    def test_unclear(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("unclear", 0.50), 5)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_UNCLEAR)
        self.assertTrue(draft.needs_review)

    def test_invalid_non_abcd(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("E", 0.80), 6)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_INVALID)
        self.assertTrue(draft.needs_review)

    def test_low_confidence(self):
        draft = normalize_choice_recognition(
            ChoiceCellOutput("A", 0.70), 7, low_confidence_threshold=0.80
        )
        self.assertEqual(
            draft.status, RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE
        )
        self.assertTrue(draft.needs_review)

    def test_high_confidence_not_low(self):
        draft = normalize_choice_recognition(
            ChoiceCellOutput("A", 0.81), 8, low_confidence_threshold=0.80
        )
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_DRAFT)
        self.assertFalse(draft.needs_review)

    def test_lowercase_input(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("ab", 0.95), 9)
        self.assertEqual(draft.normalized_text, "AB")

    def test_message_is_human_readable(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("E", 0.80), 10)
        self.assertIn("异常选项", draft.message)


if __name__ == "__main__":
    unittest.main()
