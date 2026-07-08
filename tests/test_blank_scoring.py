import unittest

from app.domain.grading import QuestionSpec, normalize_answer, score_answer, score_answer_detail


class BlankScoringTests(unittest.TestCase):
    def test_fraction_and_decimal_are_equivalent(self):
        spec = QuestionSpec(number=1, answers=normalize_answer("1/2"), points=3, answer_text="1/2", question_type="blank")
        self.assertEqual(score_answer(spec, normalize_answer("0.5"), "0.5"), (3, "correct"))

    def test_set_answer_ignores_order(self):
        spec = QuestionSpec(number=2, answers=frozenset(), points=3, answer_text="{1,2}", question_type="\u586b\u7a7a\u9898")
        self.assertEqual(score_answer(spec, frozenset(), "{2,1}"), (3, "correct"))

    def test_root_text_forms_match_without_ai(self):
        spec = QuestionSpec(number=3, answers=frozenset(), points=3, answer_text="\u6839\u53f72", question_type="blank")
        self.assertEqual(score_answer(spec, frozenset(), "sqrt(2)"), (3, "correct"))

    def test_ambiguous_interval_requires_teacher_review(self):
        spec = QuestionSpec(number=4, answers=frozenset(), points=3, answer_text="(0,1)", question_type="blank")
        detail = score_answer_detail(spec, frozenset(), "[0,1]")
        self.assertEqual(detail.status, "needs_review")
        self.assertTrue(detail.needs_review)

    def test_blank_answer_stays_blank(self):
        spec = QuestionSpec(number=5, answers=frozenset(), points=3, answer_text="2", question_type="blank")
        self.assertEqual(score_answer(spec, frozenset(), ""), (0.0, "blank"))


if __name__ == "__main__":
    unittest.main()
