"""R102A: Teacher-facing summary contract."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class TeacherFacingSummary:
    exam_id: str = ""
    batch_id: str = ""
    total_students: int = 0
    processed_students: int = 0
    ready_students: int = 0
    needs_review_students: int = 0
    blocked_students: int = 0
    total_items: int = 0
    auto_accepted_items: int = 0
    needs_review_items: int = 0
    blocking_items: int = 0
    top_review_reasons: List[str] = field(default_factory=list)
    students_needing_attention: List[str] = field(default_factory=list)
    questions_needing_attention: List[str] = field(default_factory=list)

    def to_safe_dict(self) -> dict:
        """Safe output: no API key, no base64, no raw JSON, no headers, no confidence matrix."""
        return {"exam_id": self.exam_id, "batch_id": self.batch_id,
                "total_students": self.total_students,
                "ready_students": self.ready_students,
                "needs_review_students": self.needs_review_students,
                "blocked_students": self.blocked_students,
                "total_items": self.total_items,
                "auto_accepted_items": self.auto_accepted_items,
                "needs_review_items": self.needs_review_items,
                "blocking_items": self.blocking_items,
                "top_review_reasons": self.top_review_reasons[:5],
                "students_needing_attention": self.students_needing_attention[:10],
                "questions_needing_attention": self.questions_needing_attention[:10]}

    @classmethod
    def from_models(cls, batch_summary, review_queue_summary: dict,
                    evaluation_summary: dict, qwen_cost_summary: dict,
                    exam_id: str = "", batch_id: str = "",
                    student_statuses: dict | None = None) -> "TeacherFacingSummary":
        statuses = student_statuses or {}
        return cls(
            exam_id=exam_id,
            batch_id=batch_id,
            total_students=int(evaluation_summary.get("total_students", batch_summary.total_images)),
            processed_students=batch_summary.processed_images,
            ready_students=sum(1 for value in statuses.values() if value == "ready"),
            needs_review_students=sum(1 for value in statuses.values() if value == "needs_review"),
            blocked_students=sum(1 for value in statuses.values() if value == "blocked"),
            total_items=int(evaluation_summary.get("total_items", 0)),
            auto_accepted_items=batch_summary.auto_accepted_items,
            needs_review_items=batch_summary.needs_review_items,
            blocking_items=batch_summary.blocking_items,
            top_review_reasons=sorted(review_queue_summary.get("by_type", {})),
            students_needing_attention=[k for k, v in statuses.items() if v in {"needs_review", "blocked"}],
            questions_needing_attention=[str(q) for q in evaluation_summary.get("questions_needing_attention", [])],
        )
