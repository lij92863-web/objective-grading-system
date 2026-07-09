"""Error policy: behavioral decisions derived from the error catalog.

Provides conservative, deterministic helpers used by the grading gates:

* :func:`is_blocking`      – does this code block progression to official grading?
* :func:`requires_review`  – must this code be resolved in the Review Queue?

Unknown codes are mapped to :attr:`ErrorCode.INTERNAL_UNKNOWN_ERROR`, whose
flags are conservative (blocking=True, requires_review=True) so a missing /
unregistered code can never silently open a gate (constitution §18).
"""

from app.student_recognition.errors.error_catalog import get_entry
from app.student_recognition.errors.error_codes import ErrorCode


def is_blocking(code: ErrorCode) -> bool:
    """Return ``True`` if ``code`` blocks progression to official grading.

    Unknown codes map to ``INTERNAL_UNKNOWN_ERROR`` (blocking) — fail closed.
    """
    return get_entry(code).blocking


def requires_review(code: ErrorCode) -> bool:
    """Return ``True`` if ``code`` must be resolved in the Review Queue.

    Unknown codes map to ``INTERNAL_UNKNOWN_ERROR`` (requires review) — fail closed.
    """
    return get_entry(code).requires_review


def can_teacher_override(code: ErrorCode) -> bool:
    """Return ``True`` if a teacher is permitted to override ``code``."""
    return get_entry(code).can_teacher_override


def severity_of(code: ErrorCode) -> str:
    """Return the severity label for ``code``."""
    return get_entry(code).severity


def category_of(code: ErrorCode) -> str:
    """Return the category label for ``code``."""
    return get_entry(code).category
