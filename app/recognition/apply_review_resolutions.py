"""R84: Apply review resolutions to draft."""
from typing import Dict, List
from .review_queue import ReviewQueueItem
from .teacher_resolution import TeacherResolution, resolve_item
from .contracts import RecognizedSubmissionDraft


def apply_resolutions(draft: RecognizedSubmissionDraft,
                       items: List[ReviewQueueItem],
                       resolutions: Dict[str, TeacherResolution]) -> dict:
    """Return {ready, answers, blockers}."""
    still_pending = [i for i in items if not i.is_resolved() and i.item_id not in resolutions]
    still_blocking = [i for i in items if i.is_blocking() and i.item_id not in resolutions]
    if still_blocking:
        return {"ready": False, "answers": {}, "blockers": [f"BLOCKING_UNRESOLVED:{i.item_id}" for i in still_blocking]}
    if still_pending:
        return {"ready": False, "answers": {}, "blockers": [f"PENDING_UNRESOLVED:{i.item_id}" for i in still_pending]}
    if draft.identity_status in ("missing", "conflict"):
        return {"ready": False, "answers": {}, "blockers": [f"IDENTITY_{draft.identity_status.upper()}"]}
    answers = {}
    for i in items:
        if i.item_id in resolutions:
            result = resolve_item(i, resolutions[i.item_id])
            if result["status"] in ("accepted", "corrected"):
                answers[str(i.question_id)] = result["answer"]
        elif i.status == "accepted":
            answers[str(i.question_id)] = i.candidate_answer
    return {"ready": True, "answers": answers, "blockers": []}
