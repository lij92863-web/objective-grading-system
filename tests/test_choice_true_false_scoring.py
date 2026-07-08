import unittest

from app.domain.grading import QuestionSpec, normalize_answer, score_answer, score_answer_detail


class ChoiceAndTrueFalseScoringTests(unittest.TestCase):
    def test_single_choice_wrong_multi_select_stays_wrong(self):
        spec = QuestionSpec(number=1, answers=frozenset({"A"}), points=2, question_type="single_choice")
        self.assertEqual(score_answer(spec, normalize_answer("AB"), "AB"), (0.0, "wrong"))

    def test_multiple_choice_partial_and_wrong_option(self):
        spec = QuestionSpec(number=2, answers=frozenset({"A", "C", "D"}), points=6, partial_credit=True)
        self.assertEqual(score_answer(spec, normalize_answer("AC"), "AC"), (4.0, "partial"))
        self.assertEqual(score_answer(spec, normalize_answer("ACE"), "ACE"), (0.0, "wrong"))

    def test_invalid_choice_is_distinct_from_wrong(self):
        spec = QuestionSpec(number=3, answers=frozenset({"A"}), points=2, question_type="single_choice")
        self.assertEqual(score_answer(spec, normalize_answer("I"), "I"), (0.0, "invalid"))

    def test_true_false_accepts_common_teacher_symbols(self):
        spec = QuestionSpec(number=4, answers=frozenset({"T"}), points=1, answer_text="\u5bf9", question_type="\u5224\u65ad\u9898")
        self.assertEqual(score_answer(spec, normalize_answer("\u221a"), "\u221a"), (1, "correct"))
        self.assertEqual(score_answer(spec, normalize_answer("\u00d7"), "\u00d7"), (0.0, "wrong"))

    def test_true_false_unrecognized_is_invalid_and_structured(self):
        spec = QuestionSpec(number=5, answers=frozenset({"F"}), points=1, question_type="true_false")
        detail = score_answer_detail(spec, normalize_answer("?"), "?")
        self.assertEqual(detail.status, "invalid")
        self.assertEqual(detail.question_type, "true_false")


if __name__ == "__main__":
    unittest.main()
