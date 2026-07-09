"""Draft validation -> ``ErrorCode`` blocking errors + ``ReviewItem`` list.

This is the single place that turns a raw ``RecognitionDraft`` into the
constitution's two structured outputs:

* ``blocking_errors`` — a list of ``ErrorCode`` (never free-form strings).
* ``review_items``    — a list of ``ReviewItem`` whose ``reason_code`` is an
  ``ErrorCode`` (never a free-form ``{"reason": "..."}``).

Per the conservative-OMR / strict-identity principles (§7/§8), ambiguous cases
become review items rather than accepted answers.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_policy import is_blocking
from app.student_recognition.identity_contract import validate_identity
from app.student_recognition.review.review_item import ReviewItem


def _rid(draft, code: ErrorCode) -> str:
    return f"{draft.job_id}:{code.value}"


def validate(
    draft, roster: Optional[Dict[str, str]] = None
) -> Tuple[List[ErrorCode], List[ReviewItem]]:
    """Validate ``draft``; return ``(blocking_errors, review_items)``."""
    blocking: List[ErrorCode] = []
    reviews: List[ReviewItem] = []

    # OMR / answer candidates: an empty candidate set is a blocking gap.
    if not getattr(draft, "candidates", None):
        blocking.append(ErrorCode.OMR_OPTION_CELL_MISSING)

    # Identity (constitution §8 strict identity).
    identity = getattr(draft, "identity", None)
    if identity is None:
        blocking.append(ErrorCode.IDENTITY_MISSING)
    else:
        sid = identity.get("student_id") if isinstance(identity, dict) else None
        name = identity.get("name") if isinstance(identity, dict) else None
        id_errors = validate_identity(sid, name, roster)
        for code in id_errors:
            if is_blocking(code):
                blocking.append(code)
            else:
                reviews.append(
                    ReviewItem(
                        item_id=_rid(draft, code),
                        reason_code=code,
                        evidence={"identity": identity},
                    )
                )

    return blocking, reviews
