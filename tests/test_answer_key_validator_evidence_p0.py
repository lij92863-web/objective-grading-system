from __future__ import annotations

import unittest

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_key_validator import validate_answer_key
from app.answer_extraction.cross_file_aligner import align_by_question_no
from app.answer_extraction.question_index_builder import QuestionIndex, QuestionIndexItem


class AnswerKeyValidatorEvidenceP0Tests(unittest.TestCase):
    def index(self, question_type: str = "single_choice") -> QuestionIndex:
        return QuestionIndex([QuestionIndexItem(1, question_type=question_type, source_file="q.json")])

    def validate(self, candidate: AnswerCandidate, question_type: str = "single_choice"):
        pool = AnswerCandidatePool()
        pool.add(candidate)
        index = self.index(question_type)
        return validate_answer_key(index, pool, align_by_question_no(index, pool))

    def test_table_without_evidence_not_accepted(self) -> None:
        report = self.validate(AnswerCandidate(1, "B", "B", source_kind="answer_table", confidence=0.99))
        self.assertEqual(report.answer_statuses[1], "needs_review")
        self.assertIn("missing_evidence_for_accepted_answer", report.warnings)

    def test_itemized_without_evidence_not_accepted(self) -> None:
        report = self.validate(AnswerCandidate(1, "B", "B", source_kind="explicit_bracket_answer", confidence=0.98))
        self.assertNotEqual(report.answer_statuses[1], "accepted")

    def test_accepted_with_warnings_requires_evidence(self) -> None:
        report = self.validate(AnswerCandidate(1, "B", "B", source_kind="answer_table", confidence=0.99), "multi_choice")
        self.assertEqual(report.answer_statuses[1], "needs_review")

    def test_llm_with_evidence_still_review(self) -> None:
        report = self.validate(AnswerCandidate(1, "B", "B", source_kind="llm_candidate", evidence_text="1.【答案】B", confidence=0.7))
        self.assertEqual(report.answer_statuses[1], "needs_review")


if __name__ == "__main__":
    unittest.main()
