"""Error codes, catalog, policy and message resolution for the SRE.

Public API:
    from app.student_recognition.errors import (
        ErrorCode, CatalogEntry, CATALOG,
        is_blocking, requires_review, message_for,
    )
"""

from app.student_recognition.errors.error_catalog import (
    CATALOG,
    CatalogEntry,
    get_entry,
)
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_message import message_for
from app.student_recognition.errors.error_policy import (
    can_teacher_override,
    category_of,
    is_blocking,
    requires_review,
    severity_of,
)

__all__ = [
    "ErrorCode",
    "CatalogEntry",
    "CATALOG",
    "get_entry",
    "is_blocking",
    "requires_review",
    "can_teacher_override",
    "severity_of",
    "category_of",
    "message_for",
]
