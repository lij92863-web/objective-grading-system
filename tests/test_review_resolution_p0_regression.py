"""R82A: P0 regression tests for review resolution safety."""
import unittest
from app.recognition.review_queue import ReviewQueueItem
from app.recognition.teacher_resolution import TeacherResolution, resolve_item
from app.recognition.apply_review_resolutions import apply_resolutions
from app.recognition.contracts import RecognizedSubmissionDraft


class ReviewResolutionP0RegressionTests(unittest.TestCase):
    def setUp(self):
        self.draft = RecognizedSubmissionDraft(student_id="S1", identity_status="confirmed")

    def test_block_submission_makes_not_ready(self):
        items = [ReviewQueueItem(item_id="i1", status="pending", severity="blocking", reason="identity_conflict")]
        r = apply_resolutions(self.draft, items, {"i1": TeacherResolution(item_id="i1", action="block_submission")})
        self.assertFalse(r["ready"])
        self.assertTrue(r["blocked_submission"])

    def test_rejected_candidate_not_in_final(self):
        items = [ReviewQueueItem(item_id="i1", question_id=1, candidate_answer="E", severity="review")]
        r = apply_resolutions(self.draft, items, {"i1": TeacherResolution(item_id="i1", action="reject_candidate")})
        self.assertFalse(r["ready"])
        self.assertNotIn("1", r["final_answers"])

    def test_unresolved_pending_not_ready(self):
        items = [ReviewQueueItem(item_id="i1", status="pending", severity="review")]
        r = apply_resolutions(self.draft, items, {})
        self.assertFalse(r["ready"])

    def test_unresolved_blocking_not_ready(self):
        items = [ReviewQueueItem(item_id="i1", status="pending", severity="blocking", reason="invalid_option")]
        r = apply_resolutions(self.draft, items, {})
        self.assertFalse(r["ready"])

    def test_identity_conflict_blocks(self):
        draft = RecognizedSubmissionDraft(student_id="S1", identity_status="conflict")
        r = apply_resolutions(draft, [], {})
        self.assertFalse(r["ready"])
        self.assertTrue(r["blocked_submission"])

    def test_item_id_mismatch_fails(self):
        items = [ReviewQueueItem(item_id="correct_id", severity="review")]
        r = apply_resolutions(self.draft, items, {"wrong_id": TeacherResolution(item_id="wrong_id", action="accept_candidate")})
        self.assertFalse(r["ready"])

    def test_accept_empty_candidate_fails(self):
        items = [ReviewQueueItem(item_id="i1", candidate_answer="", severity="review")]
        res = TeacherResolution(item_id="i1", action="accept_candidate")
        self.assertFalse(res.is_valid(items[0]))

    def test_blocking_item_cannot_accept(self):
        items = [ReviewQueueItem(item_id="i1", severity="blocking", reason="invalid_option", candidate_answer="E")]
        r = apply_resolutions(self.draft, items, {"i1": TeacherResolution(item_id="i1", action="accept_candidate")})
        self.assertFalse(r["ready"])

    def test_identity_item_cannot_simple_accept(self):
        items = [ReviewQueueItem(item_id="i1", severity="blocking", reason="identity_conflict")]
        r = apply_resolutions(self.draft, items, {"i1": TeacherResolution(item_id="i1", action="accept_candidate")})
        self.assertFalse(r["ready"])


if __name__ == "__main__": unittest.main()
