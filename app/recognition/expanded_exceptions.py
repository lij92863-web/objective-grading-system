"""R13: Expanded exception codes and queue summary.

Adds structured error codes on top of the existing exception_queue module
without modifying it.  No legacy/compat/API imports.
"""
from typing import Any, Dict, List

EXCEPTION_LEVELS = {
    "IMAGE_MISSING": "blocking",
    "IMAGE_UNSUPPORTED": "blocking",
    "IMAGE_EMPTY": "blocking",
    "LAYOUT_MISSING_IDENTITY_ROI": "blocking",
    "LAYOUT_DUPLICATE_QUESTION": "blocking",
    "LAYOUT_MISSING_QUESTION_ROI": "blocking",
    "IDENTITY_MISSING": "blocking",
    "IDENTITY_CONFLICT": "blocking",
    "CHOICE_CONFLICT": "review",
    "CHOICE_LOW_CONFIDENCE": "review",
    "BLANK_LOW_CONFIDENCE": "review",
    "INVALID_OPTION": "blocking",
    "ENGINE_ERROR": "blocking",
    "QWEN_UNSAFE_RESPONSE": "blocking",
    "API_DISABLED": "blocking",
    "CONFIRMATION_REQUIRED": "review",
    "BLOCKING_BEFORE_GRADING": "blocking",
}


def exception_level(code: str) -> str:
    return EXCEPTION_LEVELS.get(code, "warning")


def has_blocking(codes: List[str]) -> bool:
    return any(EXCEPTION_LEVELS.get(c, "warning") == "blocking" for c in codes)


def summarize_queue(codes: List[str]) -> Dict[str, Any]:
    by_level = {"blocking": 0, "review": 0, "warning": 0}
    for c in codes:
        lv = EXCEPTION_LEVELS.get(c, "warning")
        by_level[lv] = by_level.get(lv, 0) + 1
    return {"total": len(codes), "by_level": by_level, "has_blocking": has_blocking(codes)}


def export_exception_json(codes: List[str]) -> List[Dict]:
    return [{"code": c, "level": EXCEPTION_LEVELS.get(c, "warning")} for c in codes]
