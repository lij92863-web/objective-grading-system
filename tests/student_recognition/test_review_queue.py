"""Review queue tests (constitution §9)."""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.review.review_item import ReviewItem, ReviewStatus
from app.student_recognition.review.review_queue import ReviewQueue


class TestReviewQueue(unittest.TestCase):
    def test_enqueue_pending(self):
        q = ReviewQueue()
        q.enqueue(ReviewItem(item_id="i1", reason_code=ErrorCode.OMR_WEAK_MARK))
        self.assertEqual(q.pending_count(), 1)
        self.assertTrue(q.has_unresolved())

    def test_resolve_clears_unresolved(self):
        q = ReviewQueue()
        q.enqueue(ReviewItem(item_id="i1", reason_code=ErrorCode.OMR_WEAK_MARK))
        q.resolve("i1", ReviewStatus.RESOLVED, note="ok", by="teacher")
        self.assertEqual(q.pending_count(), 0)
        self.assertFalse(q.has_unresolved())
        item = q.get("i1")
        self.assertEqual(item.resolution, ReviewStatus.RESOLVED)
        self.assertEqual(len(item.audit), 1)

    def test_get_missing_returns_none(self):
        q = ReviewQueue()
        self.assertIsNone(q.get("nope"))

    def test_roundtrip(self):
        q = ReviewQueue()
        q.enqueue(ReviewItem(item_id="i2", reason_code=ErrorCode.IDENTITY_NAME_ONLY))
        d = q.to_dict()
        q2 = ReviewQueue.from_dict(d)
        self.assertEqual(len(q2.all()), 1)
        self.assertEqual(q2.all()[0].reason_code, ErrorCode.IDENTITY_NAME_ONLY)


if __name__ == "__main__":
    unittest.main()
