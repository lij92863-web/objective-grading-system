import unittest

from app.domain.grading import (
    AnswerDraft,
    AnswerKey,
    DraftAnswerItem,
    DraftStatus,
    QuestionSpec,
    Submission,
    normalize_answer,
    run_grading_precheck,
)


class GradingPrecheckTests(unittest.TestCase):
    def test_missing_foundation_blocks_grading(self):
        report = run_grading_precheck()
        self.assertFalse(report.can_grade)
        messages = [issue.message for issue in report.blocking]
        self.assertTrue(any("\u6ca1\u6709\u5b66\u751f\u540d\u5355" in message for message in messages))
        self.assertTrue(any("\u6ca1\u6709\u6807\u51c6\u7b54\u6848" in message for message in messages))
        self.assertTrue(any("\u6ca1\u6709\u5b66\u751f\u4f5c\u7b54" in message for message in messages))

    def test_blank_and_invalid_choice_are_warnings(self):
        key = AnswerKey((QuestionSpec(number=1, answers=frozenset({"A"})), QuestionSpec(number=2, answers=frozenset({"B"}))))
        submission = Submission("S1", "Student One", {1: normalize_answer("I"), 2: frozenset()}, {1: "I", 2: ""}, (), 2)
        report = run_grading_precheck(students=["S1"], answer_key=key, submissions=[submission])
        self.assertTrue(report.can_grade)
        self.assertGreaterEqual(len(report.warnings), 2)

    def test_low_confidence_draft_requires_review_before_grading(self):
        key = AnswerKey((QuestionSpec(number=1, answers=frozenset({"A"})),))
        draft = AnswerDraft("S1", "Student One", (DraftAnswerItem(1, "A", confidence=0.4, status=DraftStatus.LOW_CONFIDENCE),))
        report = run_grading_precheck(students=["S1"], answer_key=key, draft_answers=[draft])
        self.assertFalse(report.can_grade)
        self.assertEqual(report.review_required[0].scope, "draft_answer")

    def test_duplicate_students_are_warning_not_blocker(self):
        key = AnswerKey((QuestionSpec(number=1, answers=frozenset({"A"})),))
        submission = Submission("S1", "Student One", {1: normalize_answer("A")}, {1: "A"}, (), 2)
        report = run_grading_precheck(students=["S1", "S1"], answer_key=key, submissions=[submission])
        self.assertTrue(report.can_grade)
        self.assertTrue(any(issue.scope == "students" for issue in report.warnings))


if __name__ == "__main__":
    unittest.main()
