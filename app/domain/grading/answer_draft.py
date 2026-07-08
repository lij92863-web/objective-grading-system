"""Draft answer intake models before formal grading."""

import dataclasses
from typing import Dict, Iterable, Optional, Tuple

from .models import Submission
from .normalize import normalize_answer


class DraftStatus:
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    LOW_CONFIDENCE = "low_confidence"
    CONFLICT = "conflict"
    BLANK = "blank"
    NEEDS_REVIEW = "needs_review"


@dataclasses.dataclass(frozen=True)
class DraftAnswerItem:
    question_number: int
    raw_answer: str = ""
    normalized_answer: str = ""
    confidence: Optional[float] = None
    source: str = ""
    status: str = DraftStatus.DRAFT
    original_answer: str = ""


@dataclasses.dataclass(frozen=True)
class AnswerDraft:
    student_id: str
    name: str
    items: Tuple[DraftAnswerItem, ...]
    row_number: int = 0


def confirm_draft_answer(item: DraftAnswerItem, answer: Optional[str] = None) -> DraftAnswerItem:
    raw_answer = item.raw_answer if answer is None else answer
    status = DraftStatus.BLANK if not str(raw_answer or "").strip() else DraftStatus.CONFIRMED
    return dataclasses.replace(
        item,
        raw_answer=raw_answer,
        normalized_answer="".join(sorted(normalize_answer(raw_answer))),
        status=status,
    )


def mark_low_confidence(item: DraftAnswerItem, threshold: float = 0.8) -> DraftAnswerItem:
    if item.status == DraftStatus.CONFIRMED:
        return item
    if item.confidence is not None and item.confidence < threshold:
        return dataclasses.replace(item, status=DraftStatus.LOW_CONFIDENCE)
    return item


def draft_to_submission(draft: AnswerDraft) -> Submission:
    answers: Dict[int, frozenset[str]] = {}
    raw_answers: Dict[int, str] = {}
    for item in draft.items:
        if item.status not in {DraftStatus.CONFIRMED, DraftStatus.BLANK}:
            raise ValueError(f"Draft answer Q{item.question_number} is not confirmed: {item.status}")
        raw_answers[item.question_number] = item.raw_answer
        answers[item.question_number] = normalize_answer(item.raw_answer)
    return Submission(
        student_id=draft.student_id,
        name=draft.name,
        answers=answers,
        raw_answers=raw_answers,
        extra_questions=(),
        row_number=draft.row_number,
    )


def draft_items_by_question(items: Iterable[DraftAnswerItem]) -> Dict[int, DraftAnswerItem]:
    return {item.question_number: item for item in items}
