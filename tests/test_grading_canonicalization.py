import ast
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.application.grading import (
    GradingOverride, GradingRunRequest, GradingRunResult, GradingRunStatus,
    run_grading_orchestrator,
)
from app.application.use_cases.csv_report_pipeline import _legacy_result_to_dict
from app.domain.grading import (
    AnswerKey, QuestionSpec, Submission, grade_submission, normalize_answer,
    run_grading_precheck,
)
from app.domain.grading.models import QuestionSpec as CanonicalQuestionSpec
from app.infrastructure.loaders.csv_loaders import load_answer_key, load_submissions, parse_status


ROOT = Path(__file__).resolve().parents[1]


class CanonicalGradingTests(unittest.TestCase):
    def _csv(self, directory, name, text):
        path = Path(directory) / name
        path.write_text(text, encoding="utf-8-sig")
        return path

    def test_csv_loader_returns_canonical_models(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as tmp:
            key_path = self._csv(tmp, "key.csv", "question,answer,question_type\n1,A,single_choice\n")
            sub_path = self._csv(tmp, "sub.csv", "student_id,name,Q1\nS1,N,A\n")
            key = load_answer_key(key_path)
            submission = load_submissions(sub_path, key)[0]
            self.assertIsInstance(key, AnswerKey)
            self.assertIsInstance(key.questions[0], CanonicalQuestionSpec)
            self.assertIsInstance(submission, Submission)

    def test_no_duplicate_domain_model_definitions_in_loader(self):
        path = ROOT / "app/infrastructure/loaders/csv_loaders.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        self.assertTrue(names.isdisjoint({"QuestionSpec", "AnswerKey", "Submission"}))

    def test_domain_layer_does_not_import_infrastructure_loader(self):
        for path in (ROOT / "app/domain/grading").glob("*.py"):
            self.assertNotIn("app.infrastructure", path.read_text(encoding="utf-8"))

    def test_submission_mapping_is_defensively_immutable(self):
        answers = {1: frozenset({"A"})}
        raw = {1: "A"}
        submission = Submission("S", "N", answers, raw, (), 2)
        answers[1] = frozenset({"B"})
        raw[1] = "B"
        self.assertEqual(submission.answers[1], frozenset({"A"}))
        self.assertEqual(submission.raw_answers[1], "A")
        with self.assertRaises(TypeError):
            submission.answers[1] = frozenset({"B"})
        with self.assertRaises(TypeError):
            submission.raw_answers[1] = "B"

    def test_normalize_choice_rules_do_not_guess_a_from_a1(self):
        self.assertEqual(normalize_answer("AB"), frozenset({"A", "B"}))
        self.assertEqual(normalize_answer("A,C"), frozenset({"A", "C"}))
        self.assertEqual(normalize_answer("a b"), frozenset({"A", "B"}))
        self.assertEqual(normalize_answer("A1"), frozenset({"A1"}))

    def test_invalid_choice_token_is_not_silently_corrected(self):
        key = AnswerKey((QuestionSpec(1, frozenset({"A"}), question_type="single_choice"),))
        sub = Submission("S", "N", {1: frozenset({"A1"})}, {1: "A1"}, (), 2)
        report = run_grading_precheck(answer_key=key, submissions=[sub])
        self.assertTrue(any(issue.scope == "answer" for issue in report.warnings))
        self.assertNotEqual(grade_submission(key, sub).score, 1)

    def test_empty_unknown_and_ambiguous_types_fail_closed(self):
        submission = Submission("S", "N", {}, {}, (), 2)
        cases = [
            QuestionSpec(1, frozenset(), answer_text="", question_type="blank"),
            QuestionSpec(1, frozenset({"A"}), answer_text="A", question_type="mystery"),
            QuestionSpec(1, frozenset({"X"}), answer_text="X"),
            QuestionSpec(1, frozenset({"T"}), answer_text="T"),
        ]
        for spec in cases:
            with self.subTest(spec=spec):
                report = run_grading_precheck(answer_key=AnswerKey((spec,)), submissions=[submission])
                self.assertFalse(report.can_grade)

    def test_choice_a_h_infers_legacy_type(self):
        key = AnswerKey((QuestionSpec(1, frozenset({"H"}), answer_text="H"),))
        sub = Submission("S", "N", {1: frozenset({"H"})}, {1: "H"}, (), 2)
        self.assertTrue(run_grading_precheck(answer_key=key, submissions=[sub]).can_grade)

    def test_unknown_status_is_rejected(self):
        self.assertEqual(parse_status("normal"), "normal")
        with self.assertRaises(ValueError):
            parse_status("mystery")

    def test_duplicate_issue_preserves_evidence_and_severity(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as tmp:
            identical = self._csv(
                tmp,
                "identical.csv",
                "question,answer,points,type\n"
                "1,A,1,single_choice\n"
                "1,A,1,single_choice\n",
            )
            conflict = self._csv(
                tmp,
                "conflict.csv",
                "question,answer,points,type\n"
                "1,A,1,single_choice\n"
                "1,B,2,single_choice\n",
            )
            sub = Submission("S", "N", {1: frozenset({"A"})}, {1: "A"}, (), 2)
            key = load_answer_key(identical)
            self.assertEqual(key.duplicate_issues[0].row_numbers, (2, 3))
            self.assertEqual(key.duplicate_issues[0].raw_answers, ("A", "A"))
            self.assertTrue(run_grading_precheck(answer_key=key, submissions=[sub]).can_grade)
            key = load_answer_key(conflict)
            report = run_grading_precheck(answer_key=key, submissions=[sub])
            self.assertFalse(report.can_grade)
            self.assertEqual(report.blocking[0].code, "conflicting_duplicate_question")

    def test_override_contract_is_auditable_and_restricted(self):
        with self.assertRaises(ValueError):
            GradingOverride(("missing_question_bank",), "", "reason", "now")
        with self.assertRaises(ValueError):
            GradingOverride(("missing_question_bank",), "actor", "", "now")
        with self.assertRaises(ValueError):
            GradingOverride(("unknown",), "actor", "reason", "now")
        with self.assertRaises(ValueError):
            GradingOverride(("missing_answer_key",), "actor", "reason", "now")
        override = GradingOverride(("missing_question_bank",), "actor", "reason", "now")
        self.assertEqual(override.actor, "actor")

    def test_orchestrator_is_typed_and_never_grades_blocked_input(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as tmp:
            key = self._csv(tmp, "key.csv", "question,answer,points,type\n1,A,1,single_choice\n1,B,2,single_choice\n")
            sub = self._csv(tmp, "sub.csv", "student_id,name,Q1\nS1,N,A\n")
            request = GradingRunRequest(key, sub, Path(tmp) / "out")
            with mock.patch("app.application.grading.orchestrator.grade_all") as grade_all:
                result = run_grading_orchestrator(request)
            self.assertIsInstance(result, GradingRunResult)
            self.assertEqual(result.status, GradingRunStatus.BLOCKED)
            grade_all.assert_not_called()

    def test_legacy_adapter_preserves_answer_fields(self):
        key = AnswerKey((QuestionSpec(1, frozenset({"A"}), answer_text="A", question_type="single_choice"),))
        sub = Submission("S", "N", {1: frozenset({"A"})}, {1: " a "}, (), 2)
        detail = _legacy_result_to_dict(grade_submission(key, sub))["details"][0]
        self.assertEqual(detail["raw_actual"], " a ")
        self.assertEqual(detail["student_answer"], " a ")
        self.assertNotEqual(detail["actual"], detail["raw_actual"])


if __name__ == "__main__":
    unittest.main()
