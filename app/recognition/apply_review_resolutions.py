"""R83A: Apply review resolutions to draft — hardened."""
from typing import Dict, List
from .review_queue import ReviewQueueItem
from .teacher_resolution import TeacherResolution, resolve_item, VALID_ACTIONS
from .contracts import RecognizedSubmissionDraft


def apply_resolutions(draft: RecognizedSubmissionDraft,
                       items: List[ReviewQueueItem],
                       resolutions: Dict[str, TeacherResolution]) -> dict:
    resolved = {}
    blockers = []
    blocked_submission = False

    for item in items:
        if item.item_id in resolutions:
            r = resolutions[item.item_id]
            if item.item_id != r.item_id:
                blockers.append(f"ITEM_ID_MISMATCH:{item.item_id}")
                continue
            if item.is_blocking() and r.action == "accept_candidate":
                blockers.append(f"BLOCKING_ITEM_CANNOT_ACCEPT:{item.item_id}")
                continue
            if "identity" in item.reason.lower() and r.action == "accept_candidate":
                blockers.append(f"IDENTITY_ITEM_REQUIRES_SPECIFIC_CONFIRMATION:{item.item_id}")
                continue
            try:
                result = resolve_item(item, r)
                if result["status"] == "blocked" or r.action == "block_submission":
                    blocked_submission = True
                elif result["status"] == "rejected":
                    pass  # rejected — not added to final answers
                elif result["status"] in ("accepted", "corrected"):
                    resolved[str(item.question_id)] = result["answer"]
            except ValueError as e:
                blockers.append(f"INVALID_RESOLUTION:{item.item_id}:{e}")
                continue
        else:
            if item.is_blocking():
                blockers.append(f"BLOCKING_UNRESOLVED:{item.item_id}")
            elif not item.is_resolved():
                blockers.append(f"PENDING_UNRESOLVED:{item.item_id}")

    if draft.identity_status in ("missing", "conflict"):
        blocked_submission = True
        blockers.append(f"IDENTITY_{draft.identity_status.upper()}")

    ready = not blocked_submission and len(blockers) == 0 and len(resolved) > 0
    return {"ready": ready, "final_answers": resolved, "blockers": blockers,
            "blocked_submission": blocked_submission}
