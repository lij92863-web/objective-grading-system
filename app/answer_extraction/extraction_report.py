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
        }
