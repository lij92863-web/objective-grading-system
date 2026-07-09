"""Small time helpers (ISO-8601 UTC timestamps)."""

import time
from typing import Optional


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string with second precision."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def from_iso(value: Optional[str]) -> Optional[float]:
    """Best-effort conversion of an ISO timestamp to a POSIX float; None on failure."""
    if not value:
        return None
    try:
        return time.mktime(time.strptime(value, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    except (ValueError, TypeError):
        return None
