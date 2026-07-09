"""Recognition draft model + draft validator tests (constitution §2 / B6)."""

import unittest

from app.student_recognition.drafts.draft_validator import validate
from app.student_recognition.drafts.recognition_draft import RecognitionDraft
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.review.review_item import ReviewItem, ReviewStatus
from app.student_recognition.state_model import State


class TestRecognitionDraftModel(unittest.TestCase):
    def test_roundtrip(self):
        draft = RecognitionDraft(
            job_id="job_x",
            status=State.DRAFT_CLEAN,
            candidates={"q1": "A"},
            identity={"student_id": "1", "name": "李明"},
            blocking_errors=[ErrorCode.IMG_BLUR_TOO_HIGH],
            review_items=[ReviewItem(item_id="i1", reason_code=ErrorCode.OMR_WEAK_MARK)],
        )
        d = draft.to_dict()
        back = RecognitionDraft.from_dict(d)
        self.assertEqual(back.job_id, "job_x")
        self.assertEqual(back.status, State.DRAFT_CLEAN)
        self.assertEqual(back.candidates, {"q1": "A"})
        self.assertEqual(back.blocking_errors, [ErrorCode.IMG_BLUR_TOO_HIGH])
        self.assertEqual(back.review_items[0].reason_code, ErrorCode.OMR_WEAK_MARK)


class TestDraftValidator(unittest.TestCase):
    def _draft(self, candidates=None, identity=None):
        return RecognitionDraft(
            job_id="job_v",
            candidates=candidates if candidates is not None else {},
            identity=identity,
        )

    def test_missing_identity_and_candidates_block(self):
        blocking, reviews = validate(self._draft(candidates={}, identity=None))
        self.assertIn(ErrorCode.IDENTITY_MISSING, blocking)
        self.assertIn(ErrorCode.OMR_OPTION_CELL_MISSING, blocking)
        self.assertEqual(reviews, [])

    def test_name_only_becomes_review_not_blocking(self):
        blocking, reviews = validate(
            self._draft(candidates={"q1": "A"}, identity={"student_id": None, "name": "李明"}),
            roster={"1": "李明"},
        )
        # candidates are present, so OMR_OPTION_CELL_MISSING is NOT a blocking error
        self.assertNotIn(ErrorCode.OMR_OPTION_CELL_MISSING, blocking)
        self.assertNotIn(ErrorCode.IDENTITY_NAME_ONLY, blocking)
        self.assertTrue(
            any(r.reason_code == ErrorCode.IDENTITY_NAME_ONLY for r in reviews)
        )

    def test_clean_when_valid(self):
        blocking, reviews = validate(
            self._draft(
                candidates={"q1": "A"},
                identity={"student_id": "1", "name": "李明"},
            ),
            roster={"1": "李明"},
        )
        self.assertEqual(blocking, [])
        self.assertEqual(reviews, [])

    def test_conflict_is_blocking(self):
        blocking, _ = validate(
            self._draft(
                candidates={"q1": "A"},
                identity={"student_id": "1", "name": "王五"},
            ),
            roster={"1": "李明"},
        )
        self.assertIn(ErrorCode.IDENTITY_CONFLICT, blocking)

    def test_review_items_carry_errorcode_reason(self):
        _, reviews = validate(
            self._draft(candidates={"q1": "A"}, identity={"student_id": None, "name": "李明"}),
            roster={"1": "李明"},
        )
        for r in reviews:
            self.assertIsInstance(r, ReviewItem)
            self.assertIsInstance(r.reason_code, ErrorCode)
            self.assertEqual(r.resolution, ReviewStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
