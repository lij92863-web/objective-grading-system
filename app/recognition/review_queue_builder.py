"""R86A: Build review queue from decisions + exceptions — hardened."""
import uuid
from typing import List, Dict
from .review_queue import ReviewQueueItem
from .contracts import RecognitionDecision
from .error_codes import BLOCKING_ERROR_CODES, lookup


EXCEPTION_TYPE_ITEM_TYPE = {
    "IDENTITY_CONFLICT": "identity", "IDENTITY_MISSING": "identity",
    "CHOICE_CONFLICT": "choice", "BLANK_LOW_CONFIDENCE": "blank",
    "INVALID_OPTION": "choice", "ENGINE_ERROR": "engine_error",
    "QWEN_UNSAFE_RESPONSE": "engine_error", "API_DISABLED": "engine_error",
    "LAYOUT_MISSING_IDENTITY_ROI": "layout",
    "LAYOUT_MISSING_QUESTION_ROI": "layout",
}
EXCEPTION_BLOCKING = {"IDENTITY_CONFLICT", "IDENTITY_MISSING", "INVALID_OPTION",
                       "ENGINE_ERROR", "QWEN_UNSAFE_RESPONSE", "API_DISABLED",
                       "LAYOUT_MISSING_IDENTITY_ROI", "LAYOUT_MISSING_QUESTION_ROI"}


def _infer_type(reason: str) -> str:
    if reason:
        policy = lookup(reason)
        if policy["item_type"] != "unknown":
            return policy["item_type"]
    return "choice"


def build_review_queue(decisions: List[RecognitionDecision],
                        student_ref: str = "", draft_id: str = "",
                        exceptions: List[Dict] = None) -> List[ReviewQueueItem]:
    items = []
    for d in decisions:
        if d.status == "auto_accepted" and not d.needs_review:
            continue
        exc_codes = []
        if exceptions:
            exc_codes = [e.get("code", "") for e in exceptions
                         if e.get("question_number") == d.question_number or not e.get("question_number")]
        policy_code = exc_codes[0] if exc_codes else d.reason
        item_type = lookup(policy_code)["item_type"] if policy_code else _infer_type(d.reason)
        severity = "blocking" if d.blocking or policy_code in BLOCKING_ERROR_CODES else "review"
        items.append(ReviewQueueItem(
            item_id=str(uuid.uuid4())[:8], draft_id=draft_id,
            student_ref=student_ref, question_id=d.question_number,
            item_type=item_type, candidate_answer=d.value, confidence=d.confidence,
            reason=d.reason, source_engine=",".join(d.source_engines),
            exception_codes=exc_codes, severity=severity, status="pending"))
    if exceptions:
        for exc in exceptions:
            qn = exc.get("question_number", 0)
            if qn and not any(i.question_id == qn for i in items):
                code = exc.get("code", "")
                policy = lookup(code)
                severity = policy["severity"]
                items.append(ReviewQueueItem(
                    item_id=str(uuid.uuid4())[:8], draft_id=draft_id,
                    student_ref=student_ref, question_id=qn,
                    item_type=policy["item_type"],
                    reason=code, exception_codes=[code],
                    severity=severity, status="pending"))
    return items


def summary(items: List[ReviewQueueItem]) -> dict:
    return {"total": len(items),
            "pending": sum(1 for i in items if i.is_pending()),
            "blocking": sum(1 for i in items if i.is_blocking()),
            "resolved": sum(1 for i in items if i.is_resolved()),
            "by_type": {t: sum(1 for i in items if i.item_type == t)
                        for t in set(i.item_type for i in items)}}
