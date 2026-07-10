import math
import unittest

from app.domain.grading import AnswerKey, QuestionSpec
from app.product.review.manual_resolution import TeacherAction
from app.product.scoring.final_score_policy import (
    FinalScoreInvariantError,
    validate_final_score,
)
from app.product.scoring.manual_score_policy import (
    ManualScorePolicy,
    ManualScoreValidationError,
)


class ManualScorePolicyTests(unittest.TestCase):
    def setUp(self):
        self.answer_key = AnswerKey((
            QuestionSpec(
                1,
                frozenset({"A"}),
                points=2,
                answer_text="A",
                question_type="single_choice",
            ),
        ))

    def assert_rejected(self, value, code):
        with self.assertRaises(ManualScoreValidationError) as caught:
            ManualScorePolicy.validate(
                self.answer_key,
                1,
                TeacherAction.MANUAL_SCORE,
                value,
            )
        self.assertEqual(caught.exception.code, code)

    def test_manual_score_above_question_max_is_rejected(self):
        self.assert_rejected(2.5, "manual_score_above_question_max")

    def test_negative_boolean_and_non_finite_manual_scores_are_rejected(self):
        self.assert_rejected(-1, "manual_score_below_zero")
        self.assert_rejected(True, "manual_score_boolean")
        for value in (math.nan, math.inf, -math.inf, "NaN", "inf"):
            with self.subTest(value=value):
                self.assert_rejected(value, "manual_score_non_finite")

    def test_manual_score_question_must_exist(self):
        with self.assertRaises(ManualScoreValidationError) as caught:
            ManualScorePolicy.validate(
                self.answer_key,
                99,
                TeacherAction.MANUAL_SCORE,
                1,
            )
        self.assertEqual(caught.exception.code, "manual_score_question_missing")

    def test_non_manual_action_cannot_carry_score(self):
        with self.assertRaises(ManualScoreValidationError) as caught:
            ManualScorePolicy.validate(
                self.answer_key,
                1,
                TeacherAction.MARK_WRONG,
                0,
            )
        self.assertEqual(caught.exception.code, "manual_score_action_mismatch")

    def test_valid_manual_score_is_not_clamped(self):
        self.assertEqual(
            ManualScorePolicy.validate(
                self.answer_key,
                1,
                TeacherAction.MANUAL_SCORE,
                "1.5",
            ),
            1.5,
        )


class FinalScorePolicyTests(unittest.TestCase):
    def test_final_score_range_and_finite_invariants(self):
        valid = {"score": 1, "max_score": 2, "percent": 50}
        validate_final_score(valid)
        attacks = (
            {"score": 3, "max_score": 2, "percent": 150},
            {"score": -1, "max_score": 2, "percent": -50},
            {"score": math.nan, "max_score": 2, "percent": 0},
            {"score": 0, "max_score": math.inf, "percent": 0},
            {"score": 0, "max_score": 0, "percent": 1},
        )
        for row in attacks:
            with self.subTest(row=row):
                with self.assertRaises(FinalScoreInvariantError):
                    validate_final_score(row)


if __name__ == "__main__":
    unittest.main()
