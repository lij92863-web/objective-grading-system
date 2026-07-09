"""Single Qwen Response Parser v2 — sanitized output → structured candidates.

Rules:
- Valid choice answer accepted as candidate
- Invalid option (non A-D) → invalid_option flag
- Missing question_id → malformed_response
- Extra question_id not in ROI → unexpected_question_id
- Low confidence blank → blank_low_confidence
- Identity candidate → never confirmed, always needs review
- Parser NEVER creates TeacherConfirmedSubmission
- Parser NEVER calls grade_all
- Parser NEVER generates final score
- Parser NEVER auto-corrects invalid options
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .single_sanitized_output import (
    SanitizedCandidate,
    SanitizedIdentityCandidate,
    SingleQwenSanitizedOutput,
)


VALID_CHOICE_CHARS = set("ABCD")


def parse_single_qwen_response(
    sanitized: SingleQwenSanitizedOutput,
    roi_file: Any,
    expected_question_ids: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Parse sanitized Qwen output against ROI expectations.

    Returns dict with parsed candidates, parser warnings, and exception codes.
    """
    warnings: List[str] = []
    exception_codes: List[str] = []
    parsed_candidates: List[Dict[str, Any]] = []

    # Determine expected question IDs from ROI
    if expected_question_ids is None:
        expected_question_ids = _extract_expected_ids(roi_file)

    # Check engine status
    if sanitized.engine_status != "ok":
        exception_codes.append("ENGINE_NOT_OK")
        return {
            "parsed_candidates": [],
            "parser_warnings": warnings,
            "parser_exception_codes": exception_codes,
        }

    # Build question_id → expected_type mapping
    expected_types = _extract_expected_types(roi_file)

    seen_ids: Set[str] = set()

    for candidate in sanitized.candidates:
        qid = candidate.question_id

        # Rule 6: Missing question_id
        if not qid:
            exception_codes.append("MISSING_QUESTION_ID")
            warnings.append("CANDIDATE_MISSING_QUESTION_ID")
            continue

        # Rule 7: Extra question_id not in ROI
        if qid not in expected_question_ids:
            exception_codes.append(f"UNEXPECTED_QUESTION_ID:{qid}")
            warnings.append(f"UNEXPECTED_QUESTION_ID:{qid}")
            continue

        seen_ids.add(qid)

        parsed = {
            "question_id": qid,
            "question_type": candidate.question_type,
            "answer": candidate.answer,
            "raw_text": candidate.raw_text,
            "confidence": candidate.confidence,
            "needs_review": candidate.needs_review,
            "invalid_option": candidate.invalid_option,
        }

        # Rule 2: Invalid option check
        if candidate.invalid_option:
            exception_codes.append(f"INVALID_OPTION:{qid}")
            parsed["needs_review"] = True

        # Rule 4: Invalid option for choice questions
        expected_type = expected_types.get(qid, "")
        if expected_type in ("single_choice", "multiple_choice"):
            if candidate.answer and candidate.answer not in ("blank", "unclear", "UNCLEAR", "BLANK"):
                if not all(c in VALID_CHOICE_CHARS for c in candidate.answer.upper()):
                    exception_codes.append(f"INVALID_OPTION:{qid}")
                    parsed["needs_review"] = True
                    parsed["invalid_option"] = True

        # Rule 8: Low confidence blank
        if expected_type == "blank" and candidate.confidence < 0.80:
            warnings.append(f"BLANK_LOW_CONFIDENCE:{qid}")
            parsed["needs_review"] = True

        # Low confidence in general
        if candidate.confidence < 0.80:
            parsed["needs_review"] = True

        parsed_candidates.append(parsed)

    # Check for expected IDs not found
    missing = expected_question_ids - seen_ids
    for m in sorted(missing):
        warnings.append(f"MISSING_EXPECTED_QUESTION_ID:{m}")

    # Rule 6: Identity candidate
    identity_result = None
    if sanitized.identity_candidate:
        identity_result = {
            "raw_text": sanitized.identity_candidate.raw_text,
            "student_number": sanitized.identity_candidate.student_number,
            "student_name": sanitized.identity_candidate.student_name,
            "confidence": sanitized.identity_candidate.confidence,
            "needs_review": True,  # Always needs review
            "confirmed": False,    # Never auto-confirm
        }
        warnings.append("IDENTITY_CANDIDATE_PRESENT_NOT_CONFIRMED")

    return {
        "parsed_candidates": parsed_candidates,
        "identity_result": identity_result,
        "parser_warnings": warnings,
        "parser_exception_codes": exception_codes,
    }


def _extract_expected_ids(roi_file: Any) -> Set[str]:
    ids: Set[str] = set()
    for attr in ['question_rois', 'choice_cell_rois', 'blank_rois']:
        for roi in getattr(roi_file, attr, []):
            qid = getattr(roi, 'question_id', '')
            if qid:
                ids.add(qid)
    # If no explicit IDs, infer from count
    if not ids:
        count = (len(getattr(roi_file, 'choice_cell_rois', [])) +
                 len(getattr(roi_file, 'blank_rois', [])))
        for i in range(1, count + 1):
            ids.add(f"Q{i}")
    return ids


def _normalize_roi_type(raw_type: str) -> str:
    """Map ROI types to canonical question types for validation."""
    if raw_type in ("blank",):
        return "blank"
    if raw_type in ("choice_question", "choice_cell", "single_choice", "multiple_choice"):
        return "single_choice"
    return raw_type


def _extract_expected_types(roi_file: Any) -> Dict[str, str]:
    types: Dict[str, str] = {}
    for roi in getattr(roi_file, 'question_rois', []):
        qid = getattr(roi, 'question_id', '')
        if qid:
            types[qid] = _normalize_roi_type(getattr(roi, 'roi_type', '') or 'single_choice')
    for roi in getattr(roi_file, 'choice_cell_rois', []):
        qid = getattr(roi, 'question_id', '')
        if qid and qid not in types:
            types[qid] = _normalize_roi_type(getattr(roi, 'roi_type', '') or 'single_choice')
    for roi in getattr(roi_file, 'blank_rois', []):
        qid = getattr(roi, 'question_id', '')
        if qid:
            types[qid] = 'blank'
    return types
