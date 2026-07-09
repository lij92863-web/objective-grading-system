from __future__ import annotations

import unittest

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_key_validator import ValidationReport, enforce_evidence_required, validate_answer_key
from app.answer_extraction.cross_file_aligner import AlignmentResult
from app.answer_extraction.question_index_builder import QuestionIndex, QuestionIndexItem


class EnforceEvidenceRequiredTests(unittest.TestCase):
    def _candidate(self, evidence="some evidence") -> AnswerCandidate:
        return AnswerCandidate(question_no=1, raw_answer="A", normalized_answer="A",
                               source_kind="answer_table", source_file="f.json",
                               evidence_text=evidence, confidence=0.99)

    def test_accepted_with_evidence_stays_accepted(self):
        status, warnings, reviews = enforce_evidence_required(self._candidate("ev"), "accepted")
        self.assertEqual(status, "accepted")
        self.assertEqual(warnings, [])

    def test_accepted_without_evidence_downgraded_to_review(self):
        status, warnings, reviews = enforce_evidence_required(self._candidate(""), "accepted")
        self.assertEqual(status, "needs_review")
        self.assertIn("missing_evidence_for_accepted_answer", warnings)

    def test_accepted_with_warnings_without_evidence_downgraded(self):
        status, warnings, reviews = enforce_evidence_required(self._candidate(""), "accepted_with_warnings")
        self.assertEqual(status, "needs_review")
        self.assertIn("missing_evidence_for_accepted_answer", warnings)

    def test_needs_review_without_evidence_stays_review(self):
        status, warnings, reviews = enforce_evidence_required(self._candidate(""), "needs_review")
        self.assertEqual(status, "needs_review")
        self.assertEqual(warnings, [])

    def test_blocked_without_evidence_stays_blocked(self):
        status, warnings, reviews = enforce_evidence_required(self._candidate(""), "blocked")
        self.assertEqual(status, "blocked")

    def test_review_item_created_for_missing_evidence(self):
        _, _, reviews = enforce_evidence_required(self._candidate(""), "accepted")
        self.assertTrue(any(r["type"] == "missing_evidence_for_accepted_answer" for r in reviews))

    def test_none_evidence_treated_as_missing(self):
        status, warnings, _ = enforce_evidence_required(self._candidate(None), "accepted")
        self.assertEqual(status, "needs_review")


class ValidatorStatusModelTests(unittest.TestCase):
    def _qi(self, question_no=1, qtype="single_choice") -> QuestionIndex:
        return QuestionIndex([QuestionIndexItem(question_no=question_no, question_type=qtype)])

    def _pool(self, question_no=1, answer="A", source="answer_table", evidence="ev", confidence=0.99) -> AnswerCandidatePool:
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(question_no=question_no, raw_answer=answer, normalized_answer=answer,
                                  source_kind=source, source_file="f.json", evidence_text=evidence,
                                  confidence=confidence))
        return pool

    def _align(self) -> AlignmentResult:
        return AlignmentResult()

    def test_llm_candidate_goes_to_review(self):
        pool = self._pool(source="llm_candidate")
        report = validate_answer_key(self._qi(), pool, self._align())
        self.assertEqual(report.answer_statuses[1], "needs_review")

    def test_single_choice_multi_answer_blocked(self):
        pool = self._pool(answer="AB")
        report = validate_answer_key(self._qi(1, "single_choice"), pool, self._align())
        self.assertIn("single_choice_multi_answer", report.blocking_errors)

    def test_multi_choice_single_letter_accepted_with_warnings(self):
        pool = self._pool(answer="B")
        report = validate_answer_key(self._qi(1, "multi_choice"), pool, self._align())
        self.assertEqual(report.answer_statuses[1], "accepted_with_warnings")

    def test_blank_pure_choice_review(self):
        pool = self._pool(answer="A", evidence="ev")
        report = validate_answer_key(self._qi(1, "blank"), pool, self._align())
        self.assertEqual(report.answer_statuses[1], "needs_review")

    def test_solution_choice_review(self):
        pool = self._pool(answer="C", evidence="ev")
        report = validate_answer_key(self._qi(1, "solution"), pool, self._align())
        self.assertEqual(report.answer_statuses[1], "needs_review")

    def test_blocking_errors_set_status_blocked(self):
        pool = self._pool(answer="AB")
        report = validate_answer_key(self._qi(1, "single_choice"), pool, self._align())
        self.assertEqual(report.status, "blocked")

    def test_review_items_set_status_needs_review(self):
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(question_no=1, raw_answer="A", normalized_answer="A",
                                  source_kind="answer_table", source_file="f.json",
                                  evidence_text="", confidence=0.99))
        report = validate_answer_key(self._qi(), pool, self._align())
        self.assertEqual(report.status, "needs_review")

    def test_missing_answer_generates_review_item(self):
        pool = self._pool(question_no=2)
        qi = self._qi(question_no=1)
        align = AlignmentResult(missing_answers=[1])
        report = validate_answer_key(qi, pool, align)
        self.assertTrue(any(r["type"] == "missing_answer" for r in report.review_items))

    def test_no_issues_gives_accepted(self):
        report = validate_answer_key(self._qi(), self._pool(), self._align())
        self.assertEqual(report.status, "accepted")


if __name__ == "__main__":
    unittest.main()
