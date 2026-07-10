"""Single server-side authority for teacher score overrides."""

import math

from app.domain.grading import AnswerKey


class ManualScoreValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ManualScorePolicy:
    @staticmethod
    def validate(
        answer_key: AnswerKey,
        question_number: object,
        teacher_action: object,
        manual_score: object,
    ) -> float | None:
        action = getattr(teacher_action, "value", teacher_action)
        action = str(action or "")
        if action != "MANUAL_SCORE":
            if manual_score is not None:
                raise ManualScoreValidationError(
                    "manual_score_action_mismatch",
                    "Only MANUAL_SCORE may carry a manual score.",
                )
            return None
        if manual_score is None:
            raise ManualScoreValidationError(
                "manual_score_missing",
                "Manual score is required.",
            )
        if isinstance(manual_score, bool):
            raise ManualScoreValidationError(
                "manual_score_boolean",
                "Boolean is not a valid score.",
            )
        try:
            score = float(manual_score)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ManualScoreValidationError(
                "manual_score_not_numeric",
                "Manual score must be numeric.",
            ) from exc
        if not math.isfinite(score):
            raise ManualScoreValidationError(
                "manual_score_non_finite",
                "Manual score must be finite.",
            )
        if score < 0:
            raise ManualScoreValidationError(
                "manual_score_below_zero",
                "Manual score cannot be below zero.",
            )
        if isinstance(question_number, bool):
            question_number = None
        try:
            number = int(question_number)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ManualScoreValidationError(
                "manual_score_question_missing",
                "Manual score needs a valid question number.",
            ) from exc
        spec = answer_key.by_number.get(number)
        if spec is None:
            raise ManualScoreValidationError(
                "manual_score_question_missing",
                "Question does not exist in the canonical answer key.",
            )
        if not math.isfinite(spec.points) or spec.points < 0:
            raise ManualScoreValidationError(
                "manual_score_question_max_invalid",
                "Question maximum score is invalid.",
            )
        if score > spec.points:
            raise ManualScoreValidationError(
                "manual_score_above_question_max",
                "Manual score cannot exceed the question maximum.",
            )
        return score
