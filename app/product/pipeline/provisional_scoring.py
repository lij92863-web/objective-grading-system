import dataclasses
from typing import Mapping

from app.domain.grading import AnswerKey, normalize_answer, score_answer_detail


@dataclasses.dataclass(frozen=True)
class ProvisionalScore:
    score: float
    max_score: float
    question_scores: Mapping[int, float]
    readable_answers: Mapping[int, str]
    unreadable_questions: tuple[int, ...]
    official: bool = False


def build_provisional_score(
    answer_key: AnswerKey,
    answer_candidates: Mapping[int, str | None],
) -> ProvisionalScore:
    score = 0.0
    question_scores: dict[int, float] = {}
    readable: dict[int, str] = {}
    unreadable: list[int] = []
    for spec in answer_key.questions:
        candidate = answer_candidates.get(spec.number)
        if candidate is None:
            unreadable.append(spec.number)
            continue
        raw = str(candidate)
        detail = score_answer_detail(spec, normalize_answer(raw), raw)
        if detail.needs_review or detail.status in {"invalid", "unrecognized"}:
            unreadable.append(spec.number)
            continue
        readable[spec.number] = raw
        question_scores[spec.number] = detail.score
        score += detail.score
    return ProvisionalScore(
        score=round(score, 6),
        max_score=answer_key.total_points,
        question_scores=question_scores,
        readable_answers=readable,
        unreadable_questions=tuple(unreadable),
    )
