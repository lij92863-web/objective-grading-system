import unittest

from app.recognition.models import QwenJudgmentMock, RecognizedAnswerDraft
from app.recognition.qwen_judgment_mock import (
    apply_qwen_judgment_mock,
    should_auto_accept_qwen_judgment,
)


class QwenJudgmentMockTests(unittest.TestCase):
    # -- apply_qwen_judgment_mock -------------------------------------------

    def test_correct_high_confidence(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.96,
            reason="两者表示同一解集",
        )
        self.assertEqual(j.verdict, "correct")
        self.assertEqual(j.confidence, 0.96)

    def test_wrong_verdict(self):
        j = apply_qwen_judgment_mock(
            "x=2", "x=3", verdict="wrong", confidence=0.95, reason="mock"
        )
        self.assertEqual(j.verdict, "wrong")

    def test_invalid_verdict_raises(self):
        with self.assertRaises(ValueError):
            apply_qwen_judgment_mock("x", "y", verdict="maybe")

    def test_defaults(self):
        j = apply_qwen_judgment_mock("ans", "ans")
        self.assertEqual(j.verdict, "correct")
        self.assertEqual(j.confidence, 0.95)
        self.assertEqual(j.normalized_standard, "ans")
        self.assertEqual(j.normalized_student, "ans")

    # -- should_auto_accept_qwen_judgment -----------------------------------

    def test_auto_accept_correct_high_confidence(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.96,
            reason="same solution set",
        )
        self.assertTrue(should_auto_accept_qwen_judgment(j))

    def test_auto_accept_wrong_high_confidence(self):
        j = apply_qwen_judgment_mock(
            "x=2", "x=3", verdict="wrong", confidence=0.95,
            reason="different values",
        )
        self.assertTrue(should_auto_accept_qwen_judgment(j))

    def test_auto_accept_partial_high_confidence(self):
        j = apply_qwen_judgment_mock(
            "(x+1)(x-1)", "x^2-1", verdict="partial", confidence=0.95,
            reason="equivalent but incomplete",
        )
        self.assertTrue(should_auto_accept_qwen_judgment(j))

    def test_needs_review_not_auto_accepted(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="needs_review", confidence=0.80,
            reason="uncertain",
        )
        self.assertFalse(should_auto_accept_qwen_judgment(j))

    def test_low_confidence_not_auto_accepted(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.70,
            reason="same",
        )
        self.assertFalse(should_auto_accept_qwen_judgment(j, threshold=0.90))

    def test_empty_reason_not_auto_accepted(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.96, reason="",
        )
        self.assertFalse(should_auto_accept_qwen_judgment(j))

    def test_missing_normalized_not_auto_accepted(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.96,
            reason="same", normalized_standard="", normalized_student="",
        )
        self.assertFalse(should_auto_accept_qwen_judgment(j))

    def test_requires_review_flag_blocks(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.96,
            reason="same", requires_review=True,
        )
        self.assertFalse(should_auto_accept_qwen_judgment(j))

    def test_draft_low_confidence_blocks(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.96,
            reason="same",
        )
        draft = RecognizedAnswerDraft(
            question_number=12,
            status=RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE,
        )
        self.assertFalse(
            should_auto_accept_qwen_judgment(j, draft=draft)
        )

    def test_draft_multiple_candidates_blocks(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.96,
            reason="same",
        )
        draft = RecognizedAnswerDraft(
            question_number=12,
            candidate_answers=("x>1", "x>=1"),
        )
        self.assertFalse(
            should_auto_accept_qwen_judgment(j, draft=draft)
        )

    def test_invalid_verdict_not_auto_accepted(self):
        j = apply_qwen_judgment_mock(
            "x>1", "???", verdict="invalid", confidence=0.50, reason="unparseable",
        )
        self.assertFalse(should_auto_accept_qwen_judgment(j))


if __name__ == "__main__":
    unittest.main()
