from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _safe_path(path: str) -> str:
    return Path(path).name if path else ""


@dataclass
class ExtractionReport:
    run_id: str
    strategy: str
    file_roles: dict[str, str] = field(default_factory=dict)
    answer_layouts: dict[str, str] = field(default_factory=dict)
    question_count: int = 0
    answer_count: int = 0
    accepted_count: int = 0
    missing_answers: list[int] = field(default_factory=list)
    unexpected_answers: list[int] = field(default_factory=list)
    duplicate_answers: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)
    review_items: list[dict[str, object]] = field(default_factory=list)
    ignored_student_answer_grid_count: int = 0
    evidence_missing_count: int = 0
    explicit_bracket_answer_count: int = 0
    answer_table_count: int = 0
    itemized_answer_count: int = 0
    blank_answer_count: int = 0
    conflict_count: int = 0

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "strategy": self.strategy,
            "file_roles": {_safe_path(k): v for k, v in self.file_roles.items()},
            "answer_layouts": {_safe_path(k): v for k, v in self.answer_layouts.items()},
            "question_count": self.question_count,
            "answer_count": self.answer_count,
            "accepted_count": self.accepted_count,
            "missing_answers": list(self.missing_answers),
            "unexpected_answers": list(self.unexpected_answers),
            "duplicate_answers": list(self.duplicate_answers),
            "warnings": list(self.warnings),
            "blocking_errors": list(self.blocking_errors),
            "review_items": list(self.review_items),
            "ignored_student_answer_grid_count": self.ignored_student_answer_grid_count,
            "evidence_missing_count": self.evidence_missing_count,
            "explicit_bracket_answer_count": self.explicit_bracket_answer_count,
            "answer_table_count": self.answer_table_count,
            "itemized_answer_count": self.itemized_answer_count,
            "blank_answer_count": self.blank_answer_count,
            "conflict_count": self.conflict_count,
            "review_count": len(self.review_items),
            "blocked_count": len(self.blocking_errors),
        }
