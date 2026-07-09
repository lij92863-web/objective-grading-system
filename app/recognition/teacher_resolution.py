"""R84A: Teacher resolution actions — hardened."""
from dataclasses import dataclass
from typing import Optional

VALID_ACTIONS = {"accept_candidate", "correct_answer", "mark_blank",
                  "reject_candidate", "block_submission",
                  "confirm_identity", "block_identity"}


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
            errors.append(f"INVALID_ACTION:{self.action}")
        if self.action == "accept_candidate":
            if item and not item.candidate_answer:
                errors.append("ACCEPT_EMPTY_CANDIDATE")
        if self.action == "correct_answer":
            if not self.final_answer:
                errors.append("CORRECT_REQUIRES_FINAL_ANSWER")
        if item and item.is_blocking() and self.action == "accept_candidate":
            errors.append("BLOCKING_ITEM_CANNOT_ACCEPT")
        return errors

    def is_valid(self, item=None) -> bool:
        return len(self.validate(item)) == 0


def resolve_item(item, resolution: TeacherResolution) -> dict:
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
    elif resolution.action == "confirm_identity":
        return {"status": "accepted", "answer": ""}
    elif resolution.action == "block_identity":
        return {"status": "blocked", "answer": ""}
    raise ValueError(f"Unknown action: {resolution.action}")
