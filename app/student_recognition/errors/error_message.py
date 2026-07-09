"""Error message resolver.

:func:`message_for` returns the human-readable (Chinese) message for an error
code, sourced exclusively from the catalog. Free-form strings are never used
(constitution §1 B6). Unknown codes fall back to ``INTERNAL_UNKNOWN_ERROR``.
"""

from app.student_recognition.errors.error_catalog import get_entry
from app.student_recognition.errors.error_codes import ErrorCode


# Only the Chinese ("zh") locale is provided in this skeleton. The ``lang``
# parameter is accepted for forward compatibility and currently selects the
# catalog's ``default_message`` (Chinese) for every supported locale.
_SUPPORTED_LOCALES = ("zh", "en")


def message_for(code: ErrorCode, lang: str = "zh") -> str:
    """Return the default message for ``code``.

    Args:
        code: The error code.
        lang: Desired locale. Only ``"zh"`` is fully supported; any other value
            currently returns the Chinese default message as well.

    Returns:
        A stable, catalog-defined message string (never a free-form string).
    """
    if lang not in _SUPPORTED_LOCALES:
        # Unknown locale: stay conservative and return the canonical message.
        lang = "zh"
    return get_entry(code).default_message
