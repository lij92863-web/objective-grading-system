from __future__ import annotations

import unittest

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_key_validator import enforce_evidence_required, validate_answer_key
from app.answer_extraction.question_index_builder import QuestionIndex, QuestionIndexItem
from app.answer_extraction.cross_file_aligner import AlignmentResult


class NoEvidenceAcceptedGuardV3Tests(unittest.TestCase):
    def test_validator_rejects_accepted_without_evidence(self):
        status, warnings, reviews = enforce_evidence_required(
            AnswerCandidate(question_no=1, raw_answer="A", normalized_answer="A",
                            source_kind="answer_table", source_file="f.json",
                            evidence_text="", confidence=0.99),
            "accepted")
        self.assertEqual(status, "needs_review")
        self.assertIn("missing_evidence_for_accepted_answer", warnings)

    def test_validator_rejects_accepted_with_warnings_without_evidence(self):
        status, warnings, _ = enforce_evidence_required(
            AnswerCandidate(question_no=1, raw_answer="A", normalized_answer="A",
                            source_kind="guxuan", source_file="f.json",
                            evidence_text="", confidence=0.88),
            "accepted_with_warnings")
        self.assertEqual(status, "needs_review")

    def test_high_confidence_no_evidence_still_rejected(self):
        status, warnings, _ = enforce_evidence_required(
            AnswerCandidate(question_no=1, raw_answer="B", normalized_answer="B",
                            source_kind="answer_table", source_file="f.json",
                            evidence_text="", confidence=0.99),
            "accepted")
        self.assertEqual(status, "needs_review")

    def test_accepted_with_evidence_passes(self):
        status, warnings, _ = enforce_evidence_required(
            AnswerCandidate(question_no=1, raw_answer="B", normalized_answer="B",
                            source_kind="answer_table", source_file="f.json",
                            evidence_text="题 1 答 B", confidence=0.99),
            "accepted")
        self.assertEqual(status, "accepted")

    def test_end_to_end_no_evidence_goes_to_review(self):
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(question_no=1, raw_answer="A", normalized_answer="A",
                                  source_kind="answer_table", source_file="f.json",
                                  evidence_text="", confidence=0.99))
        qi = QuestionIndex([QuestionIndexItem(question_no=1, question_type="single_choice")])
        report = validate_answer_key(qi, pool, AlignmentResult())
        self.assertEqual(report.answer_statuses[1], "needs_review")
        self.assertEqual(report.status, "needs_review")

    def test_evidence_invariant_module_available(self):
        from app.answer_extraction.evidence_invariant import (
            validate_extraction_result_evidence,
            enforce_result_evidence_invariant,
            ACCEPTED_STATUSES,
        )
        self.assertIn("accepted", ACCEPTED_STATUSES)
        self.assertIn("accepted_with_warnings", ACCEPTED_STATUSES)

    def test_evidence_invariant_detects_violations(self):
        from app.answer_extraction.evidence_invariant import validate_extraction_result_evidence

        result = {
            "answers": {
                "1": {"validation_status": "accepted", "evidence_text": "",
                       "source_kind": "", "source_file": "", "source_span": {}},
            }
        }
        violations = validate_extraction_result_evidence(result)
        self.assertTrue(len(violations) > 0)

    def test_evidence_invariant_no_violations_for_correct(self):
        from app.answer_extraction.evidence_invariant import validate_extraction_result_evidence

        result = {
            "answers": {
                "1": {"validation_status": "accepted", "evidence_text": "题1答B",
                       "source_kind": "answer_table", "source_file": "f.json",
                       "source_span": {"table_id": "t1", "start_block": "", "end_block": ""}},
            }
        }
        violations = validate_extraction_result_evidence(result)
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
