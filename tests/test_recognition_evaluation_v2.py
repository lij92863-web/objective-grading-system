"""R40B: Evaluation v2 tests."""
import json, unittest
from app.recognition.evaluation_v2 import evaluate_recognition, EvaluationReport
from app.recognition.contracts import RecognitionRunResult, RecognitionDecision, RecognizedSubmissionDraft


class EvaluationV2Tests(unittest.TestCase):
    def _make_result(self, decisions, gold=None):
        draft = RecognizedSubmissionDraft(student_id="S1", identity_status="confirmed",
                                           decisions=decisions, ready_for_confirmation=True)
        return RecognitionRunResult(run_id="t1", drafts=[draft]), gold

    def test_no_gold_available(self):
        result, _ = self._make_result([RecognitionDecision(question_number=1, value="A", status="auto_accepted", needs_review=False)])
        report = evaluate_recognition(result)
        self.assertFalse(report.gold_available)
        self.assertIsNone(report.candidate_accuracy)

    def test_with_gold(self):
        result, gold = self._make_result(
            [RecognitionDecision(question_number=1, value="A", status="auto_accepted", needs_review=False),
             RecognitionDecision(question_number=2, value="B", status="needs_review", needs_review=True)],
            {1: "A", 2: "B"})
        report = evaluate_recognition(result, gold)
        self.assertTrue(report.gold_available)
        self.assertEqual(report.candidate_accuracy, 100.0)

    def test_false_auto_accept_detected(self):
        result, gold = self._make_result(
            [RecognitionDecision(question_number=1, value="A", status="auto_accepted", needs_review=False)],
            {1: "B"})
        report = evaluate_recognition(result, gold)
        self.assertEqual(report.false_auto_accept_count, 1)

    def test_review_rate(self):
        result, _ = self._make_result([
            RecognitionDecision(question_number=1, status="auto_accepted", needs_review=False),
            RecognitionDecision(question_number=2, status="needs_review", needs_review=True)])
        report = evaluate_recognition(result)
        self.assertEqual(report.review_rate, 50.0)

    def test_json_serializable(self):
        report = EvaluationReport(total_items=10, gold_available=False)
        s = json.dumps(report.__dict__)
        self.assertIn("gold_available", s)


if __name__ == "__main__": unittest.main()
