"""Name-field identity parser.

Parses "学号+姓名" written in the name field of an answer sheet
(e.g. ``1李明``, ``23张三``) and validates against the class roster.
"""

import re
from typing import Dict, List, Optional

from .models import StudentIdentityCandidate

# Regex: leading digits (optional) followed by name text
_IDENTITY_RE = re.compile(r"^(\d+)\s*([^\d].*)$", re.UNICODE)


def parse_student_identity(
    raw_text: str,
    roster: Optional[Dict[str, str]] = None,
    confidence: float = 1.0,
) -> StudentIdentityCandidate:
    """Parse a name-field string and optionally validate against a roster.

    Parameters
    ----------
    raw_text:
        The OCR result from the name field, e.g. ``"1李明"``.
    roster:
        Optional ``{student_id: name}`` mapping from
        ``roster_manager.load_roster()``.
    confidence:
        OCR confidence from the recognition step (0.0-1.0).

    Returns
    -------
    StudentIdentityCandidate
        Parsed result with status and message.
    """
    text = (raw_text or "").strip()
    if not text:
        return StudentIdentityCandidate(
            raw_text=text,
            status=StudentIdentityCandidate.STATUS_INVALID,
            confidence=confidence,
            message="姓名栏为空，无法解析。",
        )

    match = _IDENTITY_RE.match(text)
    if match:
        student_number = match.group(1)
        student_name = match.group(2).strip()
    else:
        # No leading digits — treat the whole text as a name
        if any("一" <= char <= "鿿" for char in text):
            student_number = ""
            student_name = text
        else:
            return StudentIdentityCandidate(
                raw_text=text,
                status=StudentIdentityCandidate.STATUS_INVALID,
                confidence=confidence,
                message="姓名栏内容无法解析，请确认。",
            )

    # Without roster we just return the parsed identity
    if roster is None:
        return StudentIdentityCandidate(
            raw_text=text,
            student_number=student_number,
            student_name=student_name,
            status="draft",
            confidence=confidence,
            message="未提供班级名单，无法校验。",
        )

    # -- roster validation --------------------------------------------------
    return _validate_against_roster(text, student_number, student_name, roster, confidence)


def _validate_against_roster(
    raw_text: str,
    student_number: str,
    student_name: str,
    roster: Dict[str, str],
    confidence: float,
) -> StudentIdentityCandidate:
    """Run the full roster-validation matrix from the architecture doc."""

    # Helper: find name in roster
    def _find_by_name(name: str) -> List[str]:
        return [sid for sid, sname in roster.items() if str(sname).strip() == name]

    matching_ids = _find_by_name(student_name)

    # Case 1: number + name both present and matching
    if student_number and student_name:
        if student_number in roster and roster[student_number] == student_name:
            return StudentIdentityCandidate(
                raw_text=raw_text,
                student_number=student_number,
                student_name=student_name,
                status=StudentIdentityCandidate.STATUS_CONFIRMED,
                confidence=confidence,
                message="序号与姓名匹配，已确认。",
                matched_student_id=student_number,
            )
        # number exists but name mismatch
        if student_number in roster and roster[student_number] != student_name:
            return StudentIdentityCandidate(
                raw_text=raw_text,
                student_number=student_number,
                student_name=student_name,
                status=StudentIdentityCandidate.STATUS_CONFLICT,
                confidence=confidence,
                message=f"姓名栏识别结果与学生名单不一致：序号 {student_number} 在名单中为 {roster[student_number]}，但识别为 {student_name}，请确认。",
            )
        # name exists but under a different number
        if matching_ids and student_number not in roster:
            return StudentIdentityCandidate(
                raw_text=raw_text,
                student_number=student_number,
                student_name=student_name,
                status=StudentIdentityCandidate.STATUS_CONFLICT,
                confidence=confidence,
                message=f"姓名 {student_name} 在名单中序号为 {matching_ids[0]}，但识别序号为 {student_number}，请确认。",
            )
        # neither number nor name found
        return StudentIdentityCandidate(
            raw_text=raw_text,
            student_number=student_number,
            student_name=student_name,
            status=StudentIdentityCandidate.STATUS_INVALID,
            confidence=confidence,
            message=f"序号 {student_number} 和姓名 {student_name} 均不在班级名单中，请确认。",
        )

    # Case 2: only name, no number
    if student_name and not student_number:
        if matching_ids:
            return StudentIdentityCandidate(
                raw_text=raw_text,
                student_name=student_name,
                status=StudentIdentityCandidate.STATUS_NEEDS_REVIEW,
                confidence=confidence,
                message=f"姓名 {student_name} 在班级名单中，但缺少序号，请确认。",
                matched_student_id=matching_ids[0],
            )
        return StudentIdentityCandidate(
            raw_text=raw_text,
            student_name=student_name,
            status=StudentIdentityCandidate.STATUS_INVALID,
            confidence=confidence,
            message=f"姓名 {student_name} 不在班级名单中，请确认。",
        )

    # Case 3: number only, no name
    if student_number and not student_name:
        if student_number in roster:
            return StudentIdentityCandidate(
                raw_text=raw_text,
                student_number=student_number,
                student_name=roster[student_number],
                status=StudentIdentityCandidate.STATUS_CONFIRMED,
                confidence=confidence,
                message="仅有序号，已按名单补全姓名。",
                matched_student_id=student_number,
            )
        return StudentIdentityCandidate(
            raw_text=raw_text,
            student_number=student_number,
            status=StudentIdentityCandidate.STATUS_INVALID,
            confidence=confidence,
            message=f"序号 {student_number} 不在班级名单中，请确认。",
        )

    # Fallback
    return StudentIdentityCandidate(
        raw_text=raw_text,
        status=StudentIdentityCandidate.STATUS_INVALID,
        confidence=confidence,
        message="姓名栏内容无法解析，请确认。",
    )
