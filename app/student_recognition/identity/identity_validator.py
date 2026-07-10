from dataclasses import dataclass
from typing import Tuple
from app.student_recognition.errors.error_codes import ErrorCode
from .identity_candidate import IdentityCandidate
@dataclass(frozen=True)
class IdentityDecision:
    status:str; candidate:IdentityCandidate; reason_codes:Tuple[ErrorCode,...]
def validate_candidate(candidate,roster,confirmed_ids=()):
    if not candidate.student_id and not candidate.name:return IdentityDecision('blocked',candidate,(ErrorCode.IDENTITY_MISSING,))
    if not candidate.student_id:return IdentityDecision('needs_review',candidate,(ErrorCode.IDENTITY_NAME_ONLY,))
    if candidate.student_id not in roster:return IdentityDecision('blocked',candidate,(ErrorCode.IDENTITY_ROSTER_NOT_FOUND,))
    if candidate.name != roster[candidate.student_id]:return IdentityDecision('blocked',candidate,(ErrorCode.IDENTITY_CONFLICT,))
    if candidate.student_id in confirmed_ids:return IdentityDecision('blocked',candidate,(ErrorCode.IDENTITY_DUPLICATE,))
    if candidate.source.startswith('fake'):return IdentityDecision('needs_review',candidate,(ErrorCode.IDENTITY_LOW_CONFIDENCE,))
    return IdentityDecision('confirmed',candidate,())
