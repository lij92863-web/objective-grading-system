"""R83: Teacher resolution actions."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TeacherResolution:
    item_id: str = ""
    action: str = ""  # accept_candidate, correct_answer, mark_blank, reject_candidate, block_submission
    final_answer: str = ""
    teacher_note: str = ""
    resolved_by: str = "teacher"
    resolved_at: str = ""


def resolve_item(item, resolution: TeacherResolution) -> dict:
    if resolution.action == "accept_candidate":
        return {"status": "accepted", "answer": item.candidate_answer}
    elif resolution.action == "correct_answer":
        if not resolution.final_answer:
            raise ValueError("correct_answer requires final_answer")
        return {"status": "corrected", "answer": resolution.final_answer}
    elif resolution.action == "mark_blank":
        return {"status": "accepted", "answer": ""}
    elif resolution.action == "reject_candidate":
        return {"status": "rejected", "answer": ""}
    elif resolution.action == "block_submission":
        return {"status": "blocked", "answer": ""}
    raise ValueError(f"Unknown action: {resolution.action}")
