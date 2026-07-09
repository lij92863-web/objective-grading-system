"""R88: Review queue acceptance tests."""
import json, unittest
from app.recognition.review_queue import ReviewQueueItem
from app.recognition.review_queue_builder import build_review_queue, summary
from app.recognition.teacher_resolution import TeacherResolution, resolve_item
from app.recognition.apply_review_resolutions import apply_resolutions
from app.recognition.review_summary import build_review_summary
from app.recognition.contracts import RecognitionDecision, RecognizedSubmissionDraft


class ReviewQueueAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.decisions = [
            RecognitionDecision(question_number=1, value="A", status="auto_accepted", needs_review=False),
            RecognitionDecision(question_number=2, value="B", status="needs_review", needs_review=True, reason="omr_qwen_conflict"),
            RecognitionDecision(question_number=3, value="E", status="invalid", blocking=True, needs_review=True, reason="invalid_option"),
        ]

    def test_queue_built(self):
        items = build_review_queue(self.decisions, "S001", "d1")
        self.assertEqual(len(items), 2)  # auto_accepted excluded
        self.assertEqual(items[0].status, "pending")
        self.assertTrue(items[1].is_blocking())

    def test_summary(self):
        items = build_review_queue(self.decisions, "S001", "d1")
        s = summary(items)
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["blocking"], 1)

    def test_teacher_resolution_accept(self):
        item = ReviewQueueItem(item_id="i1", candidate_answer="B")
        r = TeacherResolution(item_id="i1", action="accept_candidate")
        result = resolve_item(item, r)
        self.assertEqual(result["status"], "accepted")

    def test_teacher_correct(self):
        item = ReviewQueueItem(item_id="i1", candidate_answer="B")
        r = TeacherResolution(item_id="i1", action="correct_answer", final_answer="D")
        result = resolve_item(item, r)
        self.assertEqual(result["answer"], "D")

    def test_blocking_unresolved_not_ready(self):
        items = [ReviewQueueItem(item_id="i1", severity="blocking", status="pending")]
        draft = RecognizedSubmissionDraft(student_id="S1", identity_status="confirmed")
        result = apply_resolutions(draft, items, {})
        self.assertFalse(result["ready"])

    def test_all_resolved_ready(self):
        items = [ReviewQueueItem(item_id="i1", candidate_answer="B", status="pending", severity="review")]
        draft = RecognizedSubmissionDraft(student_id="S1", identity_status="confirmed")
        result = apply_resolutions(draft, items, {"i1": TeacherResolution(item_id="i1", action="accept_candidate")})
        self.assertTrue(result["ready"])

    def test_identity_not_confirmed_blocks(self):
        draft = RecognizedSubmissionDraft(student_id="S1", identity_status="conflict")
        result = apply_resolutions(draft, [], {})
        self.assertFalse(result["ready"])

    def test_review_summary_json(self):
        items = [ReviewQueueItem(item_id="i1", reason="conflict", student_ref="S1", severity="review")]
        s = build_review_summary(items)
        self.assertIn("S1", s["by_student"])
        self.assertIn("conflict", s["by_reason"])


if __name__ == "__main__": unittest.main()
