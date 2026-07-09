"""Teacher confirmation policy (constitution §9 / §10).

Encodes the rule that a draft cannot become a confirmed submission unless it has
no blocking errors, no unresolved review items, and is in a confirmed state. It
also enforces that a teacher override must carry a note (no silent override).
"""

from typing import List, Tuple

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.review.review_item import ReviewItem, ReviewStatus
from app.student_recognition.state_model import CONFIRMED_STATES, State


def teacher_can_confirm(draft) -> Tuple[bool, List[ErrorCode]]:
    """Return (allowed, blocking reason codes) for confirming ``draft``.

    The draft may only be confirmed when it carries no ``blocking_errors``, no
    unresolved ``review_items``, and is already in a confirmed state.
    """
    reasons: List[ErrorCode] = []
    if getattr(draft, "blocking_errors", None):
        reasons.append(ErrorCode.DRAFT_HAS_BLOCKING_ERRORS)
    if any(not _is_resolved(r) for r in getattr(draft, "review_items", [])):
        reasons.append(ErrorCode.DRAFT_HAS_UNRESOLVED_REVIEW)
    if draft.status not in CONFIRMED_STATES:
        reasons.append(ErrorCode.TEACHER_CONFIRMATION_REQUIRED)
    return (len(reasons) == 0), reasons


def _is_resolved(item: ReviewItem) -> bool:
    return item.resolution == ReviewStatus.RESOLVED


def override_requires_note(note: str) -> bool:
    """A teacher override must include a non-empty note (constitution §9)."""
    return bool((note or "").strip())
