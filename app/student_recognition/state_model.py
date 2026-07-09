"""State model: the single source of truth for job/draft lifecycle states.

Constitution references:
  * §2 / §3  - four-layer lifecycle, ~30 states, legal + forbidden transitions.
  * §9.1     - all status strings come from here (no scattered ``"ok"/"done"``).
  * B6       - states are an ``ErrorCode``-style enum whose value == name so they
              round-trip through JSON unchanged.

This module contains ONLY state definitions and transition rules. It must never
import business modules (capture / omr / drafts / grading_bridge). The pipeline's
``state_machine`` orchestrates transitions using this model.
"""

from enum import Enum
from typing import Dict, FrozenSet, Set

from app.student_recognition.errors.error_codes import ErrorCode


class State(str, Enum):
    """Stable lifecycle states (value == name, JSON round-trippable)."""

    # ---- Capture layer ----
    JOB_CREATED = "job_created"
    UPLOADED = "uploaded"
    IMAGE_QUALITY_CHECKED = "image_quality_checked"
    IMAGE_QUALITY_FAILED = "image_quality_failed"
    PAGE_LOCATED = "page_located"
    PAGE_LOCATE_FAILED = "page_locate_failed"
    NORMALIZED = "normalized"
    CROPS_GENERATED = "crops_generated"
    ROI_MAPPED = "roi_mapped"
    OMR_RECOGNIZED = "omr_recognized"

    # ---- Draft layer ----
    DRAFT_CREATED = "draft_created"
    DRAFT_CLEAN = "draft_clean"
    DRAFT_HAS_REVIEW_ITEMS = "draft_has_review_items"
    DRAFT_BLOCKED = "draft_blocked"

    # ---- Confirmation layer ----
    NEEDS_REVIEW = "needs_review"
    TEACHER_REVIEWING = "teacher_reviewing"
    TEACHER_CONFIRMED = "teacher_confirmed"
    TEACHER_OVERRIDDEN = "teacher_overridden"
    TEACHER_REJECTED = "teacher_rejected"

    # ---- Grading / official layer ----
    GRADING_READY = "grading_ready"
    GRADING_IN_PROGRESS = "grading_in_progress"
    GRADING_COMPLETED = "grading_completed"
    PROVISIONAL_GRADED = "provisional_graded"
    EXAM_OFFICIAL_REPORT_PENDING = "exam_official_report_pending"
    OFFICIAL_REPORT_GENERATED = "official_report_generated"
    OFFICIAL_GRADED = "official_graded"

    # ---- Lifecycle ----
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ARCHIVED = "archived"


# Convenience sets ---------------------------------------------------------
TERMINAL_STATES: FrozenSet[State] = frozenset(
    {State.CANCELLED, State.FAILED, State.ARCHIVED}
)

CONFIRMED_STATES: FrozenSet[State] = frozenset(
    {State.TEACHER_CONFIRMED, State.TEACHER_OVERRIDDEN}
)

# Explicitly forbidden jumps (constitution §3.4 F1-F7) ---------------------
FORBIDDEN_TRANSITIONS: FrozenSet[tuple] = frozenset(
    {
        (State.DRAFT_BLOCKED, State.GRADING_READY),          # F1
        (State.NEEDS_REVIEW, State.GRADING_READY),           # F2 (bypass confirm)
        (State.NEEDS_REVIEW, State.OFFICIAL_GRADED),         # F3 (direct official)
        (State.TEACHER_REJECTED, State.GRADING_READY),       # F4
        (State.DRAFT_CREATED, State.OFFICIAL_REPORT_GENERATED),  # F6
        (State.DRAFT_CLEAN, State.OFFICIAL_REPORT_GENERATED),    # F6
        (State.PROVISIONAL_GRADED, State.OFFICIAL_GRADED),   # F7 (fake official)
    }
)


class IllegalTransitionError(Exception):
    """Raised when a state transition is not allowed.

    Carries the offending ``from``/``to`` states and a default ``ErrorCode`` so
    callers can record it without inventing a free-form reason string.
    """

    def __init__(self, frm: State, to: State, code: ErrorCode = ErrorCode.INTERNAL_UNKNOWN_ERROR):
        self.frm = frm
        self.to = to
        self.code = code
        super().__init__(f"illegal transition {frm.value} -> {to.value}")


# Legal transition map -----------------------------------------------------
_ALLOWED: Dict[State, Set[State]] = {
    State.JOB_CREATED: {State.UPLOADED},
    State.UPLOADED: {State.IMAGE_QUALITY_CHECKED, State.IMAGE_QUALITY_FAILED},
    State.IMAGE_QUALITY_CHECKED: {State.PAGE_LOCATED},
    State.IMAGE_QUALITY_FAILED: {State.RETRYING, State.CANCELLED},
    State.PAGE_LOCATED: {State.NORMALIZED},
    State.PAGE_LOCATE_FAILED: {State.RETRYING, State.CANCELLED},
    State.NORMALIZED: {State.CROPS_GENERATED},
    State.CROPS_GENERATED: {State.ROI_MAPPED},
    State.ROI_MAPPED: {State.OMR_RECOGNIZED},
    State.OMR_RECOGNIZED: {State.DRAFT_CREATED},
    State.DRAFT_CREATED: {
        State.DRAFT_CLEAN,
        State.DRAFT_HAS_REVIEW_ITEMS,
        State.DRAFT_BLOCKED,
    },
    State.DRAFT_CLEAN: {State.TEACHER_CONFIRMED},
    State.DRAFT_HAS_REVIEW_ITEMS: {State.NEEDS_REVIEW},
    State.NEEDS_REVIEW: {State.TEACHER_REVIEWING},
    State.TEACHER_REVIEWING: {
        State.TEACHER_CONFIRMED,
        State.TEACHER_OVERRIDDEN,
        State.TEACHER_REJECTED,
    },
    State.TEACHER_OVERRIDDEN: {State.TEACHER_CONFIRMED},
    State.TEACHER_REJECTED: {State.NEEDS_REVIEW},
    State.DRAFT_BLOCKED: {State.CANCELLED, State.RETRYING, State.ARCHIVED},
    State.TEACHER_CONFIRMED: {State.GRADING_READY},
    State.GRADING_READY: {State.GRADING_IN_PROGRESS},
    State.GRADING_IN_PROGRESS: {State.GRADING_COMPLETED},
    State.GRADING_COMPLETED: {State.PROVISIONAL_GRADED},
    State.PROVISIONAL_GRADED: {State.EXAM_OFFICIAL_REPORT_PENDING},
    State.EXAM_OFFICIAL_REPORT_PENDING: {State.OFFICIAL_REPORT_GENERATED},
    State.OFFICIAL_REPORT_GENERATED: {State.OFFICIAL_GRADED},
    State.RETRYING: {State.JOB_CREATED},
    State.CANCELLED: {State.ARCHIVED},
    State.FAILED: {State.ARCHIVED},
    State.OFFICIAL_GRADED: {State.ARCHIVED},
}


def can_transition(frm: State, to: State) -> bool:
    """Return ``True`` if ``frm -> to`` is a legal single-step transition."""
    if not isinstance(frm, State) or not isinstance(to, State):
        return False
    if frm == to:
        return True  # idempotent re-apply is allowed
    if (frm, to) in FORBIDDEN_TRANSITIONS:
        return False
    if to in TERMINAL_STATES and frm not in TERMINAL_STATES:
        return True  # any non-terminal state may terminate
    return to in _ALLOWED.get(frm, set())


def apply_transition(job, to: State) -> None:
    """Mutate ``job.status`` to ``to`` if legal, appending a transition event.

    The ``job`` must expose ``status`` (a ``State``) and an ``append_event``
    method. This is deliberately a *single-step* operation: there is no API to
    jump multiple states at once (constitution §3.4 F5).
    """
    if isinstance(to, str):
        to = State(to)
    frm = job.status
    if not can_transition(frm, to):
        raise IllegalTransitionError(frm, to)
    job.status = to
    try:
        job.append_event("transition", {"from": frm.value, "to": to.value})
    except AttributeError:
        pass
