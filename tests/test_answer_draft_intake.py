import unittest

from app.domain.grading import (
    AnswerDraft,
    DraftAnswerItem,
    DraftStatus,
    confirm_draft_answer,
    draft_to_submission,
    mark_low_confidence,
)


class AnswerDraftIntakeTests(unittest.TestCase):
    def test_confirmed_draft_converts_to_submission(self):
        item = confirm_draft_answer(DraftAnswerItem(question_number=1, raw_answer="a", confidence=0.99))
        draft = AnswerDraft("S1", "Student One", (item,), row_number=2)
        submission = draft_to_submission(draft)
        self.assertEqual(submission.answers[1], frozenset({"A"}))
        self.assertEqual(submission.raw_answers[1], "a")

    def test_low_confidence_draft_must_not_convert(self):
        item = mark_low_confidence(DraftAnswerItem(question_number=1, raw_answer="A", confidence=0.5))
        draft = AnswerDraft("S1", "Student One", (item,))
        with self.assertRaises(ValueError):
            draft_to_submission(draft)

    def test_conflict_draft_must_not_convert(self):
        item = DraftAnswerItem(question_number=1, raw_answer="A/B", status=DraftStatus.CONFLICT)
        draft = AnswerDraft("S1", "Student One", (item,))
        with self.assertRaises(ValueError):
            draft_to_submission(draft)

    def test_confirmed_blank_preserves_blank_state(self):
        item = confirm_draft_answer(DraftAnswerItem(question_number=2), "")
        self.assertEqual(item.status, DraftStatus.BLANK)
        submission = draft_to_submission(AnswerDraft("S1", "Student One", (item,)))
        self.assertEqual(submission.answers[2], frozenset())
        self.assertEqual(submission.raw_answers[2], "")


if __name__ == "__main__":
    unittest.main()
