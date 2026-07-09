from __future__ import annotations

import unittest
from pathlib import Path

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_key_validator import validate_answer_key
from app.answer_extraction.cross_file_aligner import align_by_question_no
from app.answer_extraction.extraction_engine import extract_answer_key, load_document
from app.answer_extraction.question_index_builder import build_question_index

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "tests" / "fixtures" / "answer_extraction" / "matrix_v3"


class AnswerExtractionMatrixV3Tests(unittest.TestCase):
    def test_matrix_has_at_least_twenty_fixtures(self) -> None:
        self.assertGreaterEqual(len(list(MATRIX.glob("*.json"))), 20)

    def test_core_matrix_scenarios(self) -> None:
        accepted = extract_answer_key([str(MATRIX / "04_same_file_itemized_real_brackets.json")]).to_safe_dict()
        self.assertEqual(accepted["status"], "accepted")
        self.assertIn("【答案】", accepted["answers"]["1"]["evidence_text"])
        unexpected = extract_answer_key([str(MATRIX / "15_unexpected_answer_number.json")]).to_safe_dict()
        self.assertIn("unexpected_answer_number", unexpected["blocking_errors"])
        single_multi = extract_answer_key([str(MATRIX / "16_single_choice_multi_answer.json")]).to_safe_dict()
        self.assertIn("single_choice_multi_answer", single_multi["report"]["blocking_errors"])
        blank_review = extract_answer_key([str(MATRIX / "17_blank_pure_choice_review.json")]).to_safe_dict()
        self.assertEqual(blank_review["answers"]["12"]["validation_status"], "needs_review")

    def test_direct_no_evidence_candidate_review(self) -> None:
        index = build_question_index(load_document(MATRIX / "04_same_file_itemized_real_brackets.json"))
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(1, "B", "B", source_kind="answer_table", confidence=0.99))
        report = validate_answer_key(index, pool, align_by_question_no(index, pool))
        self.assertEqual(report.answer_statuses[1], "needs_review")


if __name__ == "__main__":
    unittest.main()
