import unittest

from app.recognition.blank_mock import normalize_blank_recognition
from app.recognition.models import MockBlankOutput, RecognizedAnswerDraft


class BlankMockTests(unittest.TestCase):
    def test_normal_fraction_with_latex(self):
        output = MockBlankOutput(
            raw_text="1/2", latex="\\frac{1}{2}", confidence=0.92, status="recognized"
        )
        draft = normalize_blank_recognition(output, 12)
        self.assertEqual(draft.raw_text, "1/2")
        self.assertEqual(draft.latex, "\\frac{1}{2}")
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_DRAFT)
        self.assertFalse(draft.needs_review)

    def test_blank(self):
        output = MockBlankOutput(status="blank")
        draft = normalize_blank_recognition(output, 13)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_BLANK)
        self.assertFalse(draft.needs_review)

    def test_unclear(self):
        output = MockBlankOutput(raw_text="unclear", confidence=0.40, status="unclear")
        draft = normalize_blank_recognition(output, 14)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_UNCLEAR)
        self.assertTrue(draft.needs_review)

    def test_unclear_status_field(self):
        output = MockBlankOutput(raw_text="something", confidence=0.45, status="unclear")
        draft = normalize_blank_recognition(output, 14)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_UNCLEAR)
        self.assertTrue(draft.needs_review)

    def test_low_confidence(self):
        output = MockBlankOutput(
            raw_text="x+1", confidence=0.70, status="recognized"
        )
        draft = normalize_blank_recognition(
            output, 15, low_confidence_threshold=0.80
        )
        self.assertEqual(
            draft.status, RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE
        )
        self.assertTrue(draft.needs_review)

    def test_latex_field_preserved(self):
        output = MockBlankOutput(
            raw_text="x^2+1",
            latex="x^{2}+1",
            confidence=0.94,
            status="recognized",
        )
        draft = normalize_blank_recognition(output, 16)
        self.assertEqual(draft.latex, "x^{2}+1")
        self.assertEqual(draft.confidence, 0.94)

    def test_empty_raw_text_treated_as_blank(self):
        output = MockBlankOutput(raw_text="", confidence=0.99, status="recognized")
        draft = normalize_blank_recognition(output, 17)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_BLANK)

    def test_question_type_is_blank(self):
        output = MockBlankOutput(
            raw_text="42", confidence=0.95, status="recognized"
        )
        draft = normalize_blank_recognition(output, 18)
        self.assertEqual(draft.question_type, "blank")


if __name__ == "__main__":
    unittest.main()
