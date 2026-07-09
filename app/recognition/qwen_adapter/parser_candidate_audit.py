"""Parser Candidate Audit — structural audit of parsed Qwen candidates.

Audits parsed candidates for safety before they can proceed to review queue.
ready_for_grading is ALWAYS false — grading requires teacher confirmation.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class ParserCandidateAudit:
    audit_version: int = 1
    request_id: str = ""
    candidate_count: int = 0
    valid_candidate_count: int = 0
    review_candidate_count: int = 0
    blocking_candidate_count: int = 0
    unexpected_question_id_count: int = 0
    missing_question_id_count: int = 0
    invalid_option_count: int = 0
    identity_candidate_count: int = 0
    blank_low_confidence_count: int = 0
    exception_codes: List[str] = field(default_factory=list)
    ready_for_review_queue: bool = False
    ready_for_grading: bool = False  # ALWAYS false

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def audit_parser_candidates(
    parsed_result: Dict[str, Any],
    sanitized: Any,
    request_id: str = "",
) -> ParserCandidateAudit:
    """Audit parsed candidates for safety.

    ready_for_grading is ALWAYS False.
    ready_for_review_queue can be True if no blocking conditions.
    """
    candidates = parsed_result.get("parsed_candidates", [])
    exception_codes = list(parsed_result.get("parser_exception_codes", []))

    valid_count = sum(1 for c in candidates if not c.get("needs_review", False))
    review_count = sum(1 for c in candidates if c.get("needs_review", False))

    # Count exception types
    unexpected_count = sum(1 for e in exception_codes if e.startswith("UNEXPECTED_QUESTION_ID"))
    missing_count = sum(1 for e in exception_codes if e.startswith("MISSING_QUESTION_ID"))
    invalid_count = sum(1 for e in exception_codes if e.startswith("INVALID_OPTION"))
    identity_count = 1 if parsed_result.get("identity_result") else 0

    # Determine readiness
    blocking = (
        invalid_count > 0 or
        unexpected_count > 0 or
        identity_count > 0 or
        sanitized.engine_status != "ok"
    )

    return ParserCandidateAudit(
        request_id=request_id,
        candidate_count=len(candidates),
        valid_candidate_count=valid_count,
        review_candidate_count=review_count,
        blocking_candidate_count=len(candidates) - valid_count if blocking else 0,
        unexpected_question_id_count=unexpected_count,
        missing_question_id_count=missing_count,
        invalid_option_count=invalid_count,
        identity_candidate_count=identity_count,
        blank_low_confidence_count=sum(1 for e in exception_codes if "BLANK_LOW_CONFIDENCE" in e),
        exception_codes=exception_codes,
        ready_for_review_queue=not blocking and len(candidates) > 0,
        ready_for_grading=False,  # ALWAYS false
    )
