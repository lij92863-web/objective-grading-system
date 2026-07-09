from __future__ import annotations

import unittest

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_key_validator import enforce_evidence_required, validate_answer_key
from app.answer_extraction.cross_file_aligner import AlignmentResult
from app.answer_extraction.evidence_invariant import (
    validate_extraction_result_evidence,
    enforce_result_evidence_invariant,
)
from app.answer_extraction.question_index_builder import QuestionIndex, QuestionIndexItem
from app.answer_extraction.status_model import (
    STATUS_ACCEPTED, STATUS_ACCEPTED_WITH_WARNINGS,
    STATUS_NEEDS_REVIEW, FINAL_ACCEPTED_STATUSES,
)


class EvidenceInvariantEngineOutputP0Tests(unittest.TestCase):
    def test_validator_rejects_accepted_without_evidence(self):
        status, warnings, reviews = enforce_evidence_required(
            AnswerCandidate(question_no=1, raw_answer="A", normalized_answer="A",
                            source_kind="answer_table", source_file="f.json",
                            evidence_text="", confidence=0.99),
            STATUS_ACCEPTED)
        self.assertEqual(status, STATUS_NEEDS_REVIEW)
        self.assertIn("missing_evidence_for_accepted_answer", warnings)

    def test_validator_rejects_accepted_with_warnings_without_evidence(self):
        status, warnings, _ = enforce_evidence_required(
            AnswerCandidate(question_no=1, raw_answer="A", normalized_answer="A",
                            source_kind="guxuan", source_file="f.json",
                            evidence_text="", confidence=0.88),
            STATUS_ACCEPTED_WITH_WARNINGS)
        self.assertEqual(status, STATUS_NEEDS_REVIEW)

    def test_engine_output_no_evidence_not_accepted(self):
        result = {
            "answers": {
                "1": {"validation_status": STATUS_ACCEPTED, "evidence_text": "",
                       "source_kind": "", "source_file": "", "source_span": {}},
            }
        }
        violations = validate_extraction_result_evidence(result)
        self.assertTrue(len(violations) > 0)

    def test_enforce_downgrades_accepted_to_needs_review(self):
        result = {
            "status": STATUS_ACCEPTED,
            "answers": {
                "1": {"validation_status": STATUS_ACCEPTED, "evidence_text": "",
                       "source_kind": "", "source_file": "", "source_span": {}},
            },
            "review_items": [],
            "review_count": 0,
        }
        enforced = enforce_result_evidence_invariant(result)
        self.assertEqual(enforced["status"], STATUS_NEEDS_REVIEW)

    def test_accepted_with_evidence_passes_invariant(self):
        result = {
            "answers": {
                "1": {"validation_status": STATUS_ACCEPTED, "evidence_text": "题1答B",
                       "source_kind": "answer_table", "source_file": "f.json",
                       "source_span": {"table_id": "t1", "start_block": "", "end_block": ""}},
            }
        }
        violations = validate_extraction_result_evidence(result)
        self.assertEqual(len(violations), 0)

    def test_accepted_with_warnings_needs_evidence_too(self):
        self.assertIn(STATUS_ACCEPTED_WITH_WARNINGS, FINAL_ACCEPTED_STATUSES)


if __name__ == "__main__":
    unittest.main()
