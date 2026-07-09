from __future__ import annotations

STATUS_ACCEPTED = "accepted"
STATUS_ACCEPTED_WITH_WARNINGS = "accepted_with_warnings"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_BLOCKED = "blocked"
STATUS_FAILED = "failed"

FINAL_ACCEPTED_STATUSES = frozenset({
    STATUS_ACCEPTED,
    STATUS_ACCEPTED_WITH_WARNINGS,
})

NON_FINAL_STATUSES = frozenset({
    STATUS_NEEDS_REVIEW,
    STATUS_BLOCKED,
    STATUS_FAILED,
})

ALL_STATUSES = frozenset({
    STATUS_ACCEPTED,
    STATUS_ACCEPTED_WITH_WARNINGS,
    STATUS_NEEDS_REVIEW,
    STATUS_BLOCKED,
    STATUS_FAILED,
})


def is_final_accepted_status(status: str) -> bool:
    """True if the status represents a final accepted (non-review, non-blocked) outcome."""
    return status in FINAL_ACCEPTED_STATUSES


def is_non_final_status(status: str) -> bool:
    """True if the status requires further action (review/blocked/failed)."""
    return status in NON_FINAL_STATUSES
