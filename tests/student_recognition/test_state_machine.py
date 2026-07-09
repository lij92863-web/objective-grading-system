"""State machine tests (constitution §3 / §9).

Covers: legal chain, forbidden jumps (F1-F7), retry / cancelled / failed, and the
rule that a worker may only move one state at a time.
"""

import unittest

from app.student_recognition.state_model import (
    IllegalTransitionError,
    State,
    apply_transition,
    can_transition,
)


class _Job:
    """Minimal object exercising apply_transition (status + events)."""

    def __init__(self, status: State):
        self.status = status
        self.events: list = []

    def append_event(self, event_type, payload=None):
        self.events.append({"type": event_type, "payload": payload or {}})


class TestStateMachine(unittest.TestCase):
    def test_full_legal_chain(self):
        job = _Job(State.JOB_CREATED)
        chain = [
            State.UPLOADED,
            State.IMAGE_QUALITY_CHECKED,
            State.PAGE_LOCATED,
            State.NORMALIZED,
            State.CROPS_GENERATED,
            State.ROI_MAPPED,
            State.OMR_RECOGNIZED,
            State.DRAFT_CREATED,
            State.DRAFT_CLEAN,
            State.TEACHER_CONFIRMED,
            State.GRADING_READY,
            State.GRADING_IN_PROGRESS,
            State.GRADING_COMPLETED,
            State.PROVISIONAL_GRADED,
            State.EXAM_OFFICIAL_REPORT_PENDING,
            State.OFFICIAL_REPORT_GENERATED,
            State.OFFICIAL_GRADED,
        ]
        for nxt in chain:
            apply_transition(job, nxt)
        self.assertEqual(job.status, State.OFFICIAL_GRADED)
        self.assertEqual(len(job.events), len(chain))

    def test_blocked_cannot_grade_ready(self):
        self.assertFalse(can_transition(State.DRAFT_BLOCKED, State.GRADING_READY))
        job = _Job(State.DRAFT_BLOCKED)
        with self.assertRaises(IllegalTransitionError):
            apply_transition(job, State.GRADING_READY)

    def test_needs_review_cannot_bypass_confirm(self):
        self.assertFalse(can_transition(State.NEEDS_REVIEW, State.GRADING_READY))
        job = _Job(State.NEEDS_REVIEW)
        with self.assertRaises(IllegalTransitionError):
            apply_transition(job, State.GRADING_READY)

    def test_needs_review_cannot_jump_official_graded(self):
        self.assertFalse(can_transition(State.NEEDS_REVIEW, State.OFFICIAL_GRADED))
        job = _Job(State.NEEDS_REVIEW)
        with self.assertRaises(IllegalTransitionError):
            apply_transition(job, State.OFFICIAL_GRADED)

    def test_direct_official_graded_forbidden(self):
        self.assertFalse(can_transition(State.JOB_CREATED, State.OFFICIAL_GRADED))
        job = _Job(State.JOB_CREATED)
        with self.assertRaises(IllegalTransitionError):
            apply_transition(job, State.OFFICIAL_GRADED)

    def test_teacher_rejected_cannot_grade_ready(self):
        self.assertFalse(can_transition(State.TEACHER_REJECTED, State.GRADING_READY))

    def test_draft_clean_cannot_skip_to_official_report(self):
        self.assertFalse(
            can_transition(State.DRAFT_CLEAN, State.OFFICIAL_REPORT_GENERATED)
        )

    def test_provisional_cannot_fake_official(self):
        self.assertFalse(
            can_transition(State.PROVISIONAL_GRADED, State.OFFICIAL_GRADED)
        )

    def test_teacher_confirmed_required_for_grading_ready(self):
        job = _Job(State.DRAFT_CLEAN)
        apply_transition(job, State.TEACHER_CONFIRMED)
        self.assertEqual(job.status, State.TEACHER_CONFIRMED)
        apply_transition(job, State.GRADING_READY)
        self.assertEqual(job.status, State.GRADING_READY)

    def test_retry_path(self):
        job = _Job(State.IMAGE_QUALITY_FAILED)
        apply_transition(job, State.RETRYING)
        apply_transition(job, State.JOB_CREATED)
        self.assertEqual(job.status, State.JOB_CREATED)

    def test_cancelled_and_failed_terminate(self):
        for terminal in (State.CANCELLED, State.FAILED):
            job = _Job(State.UPLOADED)
            apply_transition(job, terminal)
            self.assertEqual(job.status, terminal)

    def test_cannot_skip_multiple_states_at_once(self):
        # A single transition must not leap across the chain.
        job = _Job(State.JOB_CREATED)
        with self.assertRaises(IllegalTransitionError):
            apply_transition(job, State.GRADING_READY)

    def test_same_state_is_idempotent(self):
        job = _Job(State.UPLOADED)
        self.assertTrue(can_transition(State.UPLOADED, State.UPLOADED))
        apply_transition(job, State.UPLOADED)
        self.assertEqual(job.status, State.UPLOADED)


if __name__ == "__main__":
    unittest.main()
