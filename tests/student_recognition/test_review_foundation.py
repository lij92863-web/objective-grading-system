import unittest
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.review.review_item import ReviewItem,ReviewStatus
from app.student_recognition.review.review_queue import ReviewQueue
from app.student_recognition.review.confirmation_policy import override_requires_note
class TestReviewFoundation(unittest.TestCase):
    def test_unresolved_review_cannot_confirm(self):
        q=ReviewQueue();q.enqueue(ReviewItem('i',ErrorCode.OMR_WEAK_MARK));self.assertTrue(q.has_unresolved())
    def test_teacher_override_requires_note(self): self.assertFalse(override_requires_note('  '))
    def test_resolution_preserves_original_evidence_and_audits(self):
        item=ReviewItem('i',ErrorCode.OMR_ERASURE_DETECTED,evidence={'path':'crop'})
        item.resolve(ReviewStatus.RESOLVED,'accept','teacher');self.assertEqual(item.evidence,{'path':'crop'});self.assertEqual(len(item.audit),1);self.assertIsNotNone(item.resolved_at)
    def test_invalid_reason_code_rejected(self):
        with self.assertRaises(TypeError): ReviewItem('i','freeform')
if __name__=='__main__':unittest.main()
