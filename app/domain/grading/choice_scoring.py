"""Choice-question scoring helpers."""

from typing import FrozenSet, Tuple

from .models import QuestionSpec
from .normalize import allowed_options, is_choice_answer


def score_choice_answer(spec: QuestionSpec, actual: FrozenSet[str]) -> Tuple[float, str]:
    if actual and actual == spec.answers:
        return spec.points, "correct"
    if is_choice_answer(spec.answers) and not actual <= allowed_options(spec):
        return 0.0, "invalid"
    if len(spec.answers) == 1:
        return 0.0, "wrong"
    if spec.partial_credit and len(spec.answers) > 1:
        wrong_selected = actual - spec.answers
        right_selected = actual & spec.answers
        if wrong_selected:
            return 0.0, "wrong"
        if right_selected:
            partial = spec.partial_points if spec.partial_points is not None else spec.points * len(right_selected) / len(spec.answers)
            return round(partial, 6), "partial"
    return 0.0, "wrong"
