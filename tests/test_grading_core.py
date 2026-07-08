import unittest

from app.domain.grading import AnswerKey, QuestionSpec, Submission, grade_all, normalize_answer, score_answer


class GradingCoreTests(unittest.TestCase):
    def test_single_choice_keeps_legacy_tuple_contract(self):
        spec = QuestionSpec(number=1, answers=frozenset({"A"}), points=2)
        self.assertEqual(score_answer(spec, normalize_answer("A"), "A"), (2, "correct"))
        self.assertEqual(score_answer(spec, normalize_answer("B"), "B"), (0.0, "wrong"))

    def test_grade_all_returns_structured_question_result(self):
        key = AnswerKey((QuestionSpec(number=1, answers=frozenset({"A"}), points=2),))
        submission = Submission("S1", "Student One", {1: normalize_answer("A")}, {1: "A"}, (), 2)
        result = grade_all(key, [submission])[0]
        self.assertEqual(result.score, 2)
        self.assertEqual(result.details[0].question_type, "single_choice")
        self.assertEqual(result.details[0].student_answer, "A")

    def test_legacy_entry_uses_same_core(self):
        import objective_grader

        spec = objective_grader.QuestionSpec(number=1, answers=frozenset({"A"}), points=2)
        self.assertEqual(objective_grader.score_answer(spec, objective_grader.normalize_answer("A"), "A"), (2, "correct"))


if __name__ == "__main__":
    unittest.main()
