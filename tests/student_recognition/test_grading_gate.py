"""Dual-gate (grading bridge) tests (constitution §2 / §10 / B3).

Even as a skeleton, the refuse branches must be dead: a raw RecognitionDraft can
never become a confirmed submission or an official input.
"""

import unittest

from app.student_recognition.drafts.recognition_draft import RecognitionDraft
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.grading_bridge.grading_gate import (
    ExamOfficialReportGate,
    RecognitionDraftGate,
    TeacherConfirmedSubmission,
)
from app.student_recognition.review.review_item import ReviewItem, ReviewStatus
from app.student_recognition.state_model import State


def _clean_draft(status=State.DRAFT_CLEAN):
    return RecognitionDraft(
        job_id="job_g",
        status=status,
        candidates={"q1": "A"},
        identity={"student_id": "1", "name": "李明"},
    )


class TestRecognitionDraftGate(unittest.TestCase):
    def test_unconfirmed_draft_rejected(self):
        gate = RecognitionDraftGate()
        res = gate.try_pass(_clean_draft(status=State.DRAFT_CLEAN))
        self.assertFalse(res.ok)
        self.assertEqual(res.code, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)

    def test_blocking_errors_rejected(self):
        gate = RecognitionDraftGate()
        draft = _clean_draft(status=State.TEACHER_CONFIRMED)
        draft.blocking_errors.append(ErrorCode.IDENTITY_CONFLICT)
        res = gate.try_pass(draft)
        self.assertFalse(res.ok)
        self.assertEqual(res.code, ErrorCode.GRADING_BLOCKING_ERRORS_EXIST)

    def test_unresolved_review_rejected(self):
        gate = RecognitionDraftGate()
        draft = _clean_draft(status=State.TEACHER_CONFIRMED)
        draft.review_items.append(
            ReviewItem(item_id="i", reason_code=ErrorCode.OMR_WEAK_MARK)
        )
        res = gate.try_pass(draft)
        self.assertFalse(res.ok)
        self.assertEqual(res.code, ErrorCode.GRADING_UNRESOLVED_REVIEW_ITEMS)

    def test_confirmed_clean_passes(self):
        gate = RecognitionDraftGate()
        draft = _clean_draft(status=State.TEACHER_CONFIRMED)
        res = gate.try_pass(draft)
        self.assertTrue(res.ok)
        self.assertIsInstance(res.payload, TeacherConfirmedSubmission)


class TestExamOfficialReportGate(unittest.TestCase):
    def test_empty_rejected(self):
        gate = ExamOfficialReportGate()
        res = gate.try_pass([])
        self.assertFalse(res.ok)
        self.assertEqual(res.code, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)

    def test_raw_draft_rejected(self):
        gate = ExamOfficialReportGate()
        res = gate.try_pass([_clean_draft(status=State.TEACHER_CONFIRMED)])
        self.assertFalse(res.ok)
        self.assertEqual(res.code, ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)

    def test_refuse_raw_draft_explicit(self):
        gate = ExamOfficialReportGate()
        res = gate.refuse_raw_draft(_clean_draft())
        self.assertFalse(res.ok)

    def test_duplicate_student_rejected(self):
        gate = ExamOfficialReportGate()
        sub1 = TeacherConfirmedSubmission(
            job_id="j1", draft_snapshot={}, confirmed_by="t", confirmed_at="now",
            identity={"student_id": "1", "name": "李明"},
        )
        sub2 = TeacherConfirmedSubmission(
            job_id="j2", draft_snapshot={}, confirmed_by="t", confirmed_at="now",
            identity={"student_id": "1", "name": "李明"},
        )
        res = gate.try_pass([sub1, sub2])
        self.assertFalse(res.ok)
        self.assertEqual(res.code, ErrorCode.GRADING_EXAM_HAS_DUPLICATE_STUDENT)

    def test_confirmed_submissions_pass(self):
        gate = ExamOfficialReportGate()
        sub = TeacherConfirmedSubmission(
            job_id="j1", draft_snapshot={}, confirmed_by="t", confirmed_at="now",
            identity={"student_id": "1", "name": "李明"},
        )
        res = gate.try_pass([sub])
        self.assertTrue(res.ok)
        self.assertEqual(res.payload.exam_id, "exam")


if __name__ == "__main__":
    unittest.main()
