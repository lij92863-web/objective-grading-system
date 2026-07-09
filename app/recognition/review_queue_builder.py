"""R86A: Build review queue from decisions + exceptions — hardened."""
import uuid
from typing import List, Dict
from .review_queue import ReviewQueueItem
from .contracts import RecognitionDecision


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
    r = reason.lower()
    if "identity" in r: return "identity"
    if "blank" in r: return "blank"
    if "engine" in r or "qwen" in r: return "engine_error"
    if "layout" in r or "roi" in r: return "layout"
    return "choice"


def build_review_queue(decisions: List[RecognitionDecision],
                        student_ref: str = "", draft_id: str = "",
                        exceptions: List[Dict] = None) -> List[ReviewQueueItem]:
    items = []
    for d in decisions:
        if d.status == "auto_accepted" and not d.needs_review:
            continue
        severity = "blocking" if d.blocking else "review"
        item_type = _infer_type(d.reason)
        exc_codes = []
        if exceptions:
            exc_codes = [e.get("code", "") for e in exceptions
                         if e.get("question_number") == d.question_number or not e.get("question_number")]
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
                severity = "blocking" if code in EXCEPTION_BLOCKING else "review"
                items.append(ReviewQueueItem(
                    item_id=str(uuid.uuid4())[:8], draft_id=draft_id,
                    student_ref=student_ref, question_id=qn,
                    item_type=EXCEPTION_TYPE_ITEM_TYPE.get(code, "engine_error"),
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
