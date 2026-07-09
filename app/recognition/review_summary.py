"""R85: Review queue teacher-facing summary."""
from typing import Dict, List
from .review_queue import ReviewQueueItem
from .error_codes import IDENTITY_ERROR_CODES


def build_review_summary(items: List[ReviewQueueItem]) -> dict:
    by_reason: Dict[str, int] = {}
    by_student: Dict[str, int] = {}
    for i in items:
        by_reason[i.reason] = by_reason.get(i.reason, 0) + 1
        by_student[i.student_ref] = by_student.get(i.student_ref, 0) + 1
    return {"total_items": len(items),
            "pending_count": sum(1 for i in items if i.status == "pending"),
            "blocking_count": sum(1 for i in items if i.is_blocking()),
            "by_reason": by_reason, "by_student": by_student,
            "identity_blocking": sum(1 for i in items if i.is_blocking() and _is_identity_item(i)),
            "omr_qwen_conflict": sum(1 for i in items if i.reason == "omr_qwen_conflict")}


def _is_identity_item(item: ReviewQueueItem) -> bool:
    return item.item_type == "identity" or any(code in IDENTITY_ERROR_CODES for code in item.exception_codes)
