"""R117: Teacher resolution actions — item-aware validation."""
from dataclasses import dataclass
from typing import Optional

VALID_ACTIONS = {"accept_candidate", "correct_answer", "mark_blank",
                  "reject_candidate", "block_submission",
                  "confirm_identity", "correct_identity", "block_identity"}


@dataclass
class TeacherResolution:
    item_id: str = ""
    action: str = ""
    final_answer: str = ""
    teacher_note: str = ""
    resolved_by: str = "teacher"
    resolved_at: str = ""

    def validate(self, item=None) -> list:
        errors = []
        if self.action not in VALID_ACTIONS:
            return [f"INVALID_ACTION:{self.action}"]
        if item is not None:
            if self.item_id != item.item_id:
                errors.append(f"ITEM_ID_MISMATCH:expected={item.item_id},got={self.item_id}")
                return errors
            is_identity = (item.item_type == "identity" or
                           any("identity" in str(c) for c in (item.exception_codes or [])))
            is_blocking = item.is_blocking()
            if self.action == "accept_candidate":
                if is_blocking:
                    errors.append("BLOCKING_ITEM_CANNOT_ACCEPT_CANDIDATE")
                if is_identity:
                    errors.append("IDENTITY_ITEM_CANNOT_ACCEPT_CANDIDATE")
                if not item.candidate_answer:
                    errors.append("EMPTY_CANDIDATE_CANNOT_ACCEPT")
            if self.action == "confirm_identity" and not is_identity:
                errors.append("CONFIRM_IDENTITY_ONLY_FOR_IDENTITY_ITEMS")
            if self.action == "correct_identity" and not is_identity:
                errors.append("CORRECT_IDENTITY_ONLY_FOR_IDENTITY_ITEMS")
            if self.action == "block_identity" and not is_identity:
                errors.append("BLOCK_IDENTITY_ONLY_FOR_IDENTITY_ITEMS")
        else:
            if self.action == "accept_candidate":
                errors.append("ACCEPT_CANDIDATE_REQUIRES_ITEM")
        if self.action == "correct_answer" and not self.final_answer:
            errors.append("CORRECT_REQUIRES_FINAL_ANSWER")
        return errors

    def is_valid(self, item=None) -> bool:
        return len(self.validate(item)) == 0


def resolve_item(item, resolution: TeacherResolution) -> dict:
    """Resolve a review item. Raises ValueError if invalid."""
    errors = resolution.validate(item)
    if errors:
        raise ValueError(f"Invalid resolution: {errors}")
    if resolution.action == "accept_candidate":
        return {"status": "accepted", "answer": item.candidate_answer if item else ""}
    elif resolution.action == "correct_answer":
        return {"status": "corrected", "answer": resolution.final_answer}
    elif resolution.action == "mark_blank":
        return {"status": "accepted", "answer": ""}
    elif resolution.action == "reject_candidate":
        return {"status": "rejected", "answer": ""}
    elif resolution.action == "block_submission":
        return {"status": "blocked", "answer": ""}
    elif resolution.action in ("confirm_identity", "correct_identity"):
        return {"status": "accepted", "answer": resolution.final_answer}
    elif resolution.action == "block_identity":
        return {"status": "blocked", "answer": ""}
    raise ValueError(f"Unknown action: {resolution.action}")
