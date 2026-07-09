"""Identity contract: ``student_id`` priority + "1李明" contract (constitution §8).

This is a *skeleton* of the strict-identity rules. It defines the
"student_id+name" (``1李明``) contract and the blocking-rule matrix, returning
``ErrorCode`` values (never free-form strings). Real roster matching and OMR
extraction of the identity region are filled in by later stages.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.student_recognition.errors.error_codes import ErrorCode


# "1李明" contract: leading digits = student_id, remaining text = name.
IDENTITY_CONTRACT = "student_id+name"


@dataclass
class IdentityCandidate:
    student_id: Optional[str]
    name: Optional[str]
    source: str = "ocr_fallback"  # placeholder until real OMR region (§11)
    confidence: float = 0.0
    raw: str = ""

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "source": self.source,
            "confidence": self.confidence,
            "raw": self.raw,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, object]) -> "IdentityCandidate":
        return cls(
            student_id=d.get("student_id"),  # type: ignore[arg-type]
            name=d.get("name"),  # type: ignore[arg-type]
            source=d.get("source", "ocr_fallback"),  # type: ignore[arg-type]
            confidence=float(d.get("confidence", 0.0)),  # type: ignore[arg-type]
            raw=d.get("raw", ""),  # type: ignore[arg-type]
        )


def parse_identity(raw: str) -> IdentityCandidate:
    """Parse a raw identity string under the "1李明" contract.

    Leading ASCII digits are treated as the student id; the remainder is the
    name. Returns an empty ``IdentityCandidate`` when ``raw`` is blank.
    """
    raw = (raw or "").strip()
    digits = ""
    i = 0
    while i < len(raw) and raw[i].isdigit():
        digits += raw[i]
        i += 1
    name = raw[i:].strip()
    return IdentityCandidate(
        student_id=digits or None,
        name=name or None,
        raw=raw,
    )


def validate_identity(
    student_id: Optional[str],
    name: Optional[str],
    roster: Optional[Dict[str, str]],
) -> List[ErrorCode]:
    """Return the list of identity ``ErrorCode`` for ``(student_id, name)``.

    Rules (constitution §8):
      * both missing            -> IDENTITY_MISSING (blocking)
      * only name               -> IDENTITY_NAME_ONLY (review)
      * id present, no roster   -> IDENTITY_ROSTER_NOT_FOUND (blocking)
      * id not in roster        -> IDENTITY_STUDENT_ID_ONLY_UNMATCHED (blocking)
      * id in roster but name conflicts -> IDENTITY_CONFLICT (blocking)
    """
    sid = (student_id or "").strip() or None
    nm = (name or "").strip() or None
    errors: List[ErrorCode] = []

    if sid is None and nm is None:
        return [ErrorCode.IDENTITY_MISSING]
    if sid is None and nm is not None:
        return [ErrorCode.IDENTITY_NAME_ONLY]

    # student_id present from here on
    if roster is None:
        return [ErrorCode.IDENTITY_ROSTER_NOT_FOUND]
    if sid not in roster:
        return [ErrorCode.IDENTITY_STUDENT_ID_ONLY_UNMATCHED]

    expected = roster.get(sid)
    if nm is not None and expected is not None and nm != expected:
        return [ErrorCode.IDENTITY_CONFLICT]
    return errors


def check_duplicate_students(student_ids: List[Optional[str]]) -> List[ErrorCode]:
    """Return ``IDENTITY_DUPLICATE`` when the same student id appears twice."""
    present = [s for s in student_ids if s]
    dup = {s for s, c in Counter(present).items() if c > 1}
    return [ErrorCode.IDENTITY_DUPLICATE] if dup else []
