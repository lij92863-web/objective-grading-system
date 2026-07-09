from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ReviewItem:
    item_type: str
    question_no: int | None = None
    message: str = ""
    severity: str = "review"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
