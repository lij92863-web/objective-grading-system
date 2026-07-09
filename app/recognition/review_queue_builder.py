"""R82: Build review queue from decisions and exceptions."""
import uuid
from typing import List
from .review_queue import ReviewQueueItem
from .contracts import RecognitionDecision


def build_review_queue(decisions: List[RecognitionDecision],
                        student_ref: str = "", draft_id: str = "") -> List[ReviewQueueItem]:
    items = []
    for d in decisions:
        if d.status == "auto_accepted" and not d.needs_review:
            continue
        severity = "blocking" if d.blocking else "review"
        items.append(ReviewQueueItem(
            item_id=str(uuid.uuid4())[:8], draft_id=draft_id,
            student_ref=student_ref, question_id=d.question_number,
            item_type="choice", candidate_answer=d.value, confidence=d.confidence,
            reason=d.reason, source_engine=",".join(d.source_engines),
            exception_codes=[], severity=severity, status="pending"))
    return items


def summary(items: List[ReviewQueueItem]) -> dict:
    return {"total": len(items),
            "pending": sum(1 for i in items if i.status == "pending"),
            "blocking": sum(1 for i in items if i.is_blocking()),
            "resolved": sum(1 for i in items if i.is_resolved())}
