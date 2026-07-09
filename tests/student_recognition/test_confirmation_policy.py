"""Teacher confirmation policy tests (constitution §9 / §10)."""

import unittest

from app.student_recognition.drafts.recognition_draft import RecognitionDraft
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.review.confirmation_policy import (
    override_requires_note,
    teacher_can_confirm,
)
from app.student_recognition.review.review_item import ReviewItem, ReviewStatus
from app.student_recognition.state_model import State


class TestConfirmationPolicy(unittest.TestCase):
    def test_clean_confirmed_ok(self):
        draft = RecognitionDraft(
            job_id="j", status=State.TEACHER_CONFIRMED, candidates={"q1": "A"}
        )
        ok, reasons = teacher_can_confirm(draft)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_blocking_prevents_confirm(self):
        draft = RecognitionDraft(
            job_id="j", status=State.TEACHER_CONFIRMED, candidates={}
        )
        draft.blocking_errors.append(ErrorCode.IDENTITY_MISSING)
        ok, reasons = teacher_can_confirm(draft)
        self.assertFalse(ok)
        self.assertIn(ErrorCode.DRAFT_HAS_BLOCKING_ERRORS, reasons)

    def test_unresolved_review_prevents_confirm(self):
        draft = RecognitionDraft(
            job_id="j",
            status=State.TEACHER_CONFIRMED,
            candidates={"q1": "A"},
            review_items=[
                ReviewItem(item_id="i", reason_code=ErrorCode.OMR_WEAK_MARK)
            ],
        )
        ok, reasons = teacher_can_confirm(draft)
        self.assertFalse(ok)
        self.assertIn(ErrorCode.DRAFT_HAS_UNRESOLVED_REVIEW, reasons)

    def test_not_confirmed_state_prevents(self):
        draft = RecognitionDraft(job_id="j", status=State.DRAFT_CLEAN, candidates={"q1": "A"})
        ok, reasons = teacher_can_confirm(draft)
        self.assertFalse(ok)
        self.assertIn(ErrorCode.TEACHER_CONFIRMATION_REQUIRED, reasons)

    def test_override_requires_note(self):
        self.assertFalse(override_requires_note(""))
        self.assertTrue(override_requires_note("manual fix"))


if __name__ == "__main__":
    unittest.main()
