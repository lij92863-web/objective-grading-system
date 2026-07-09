from __future__ import annotations

import unittest

from app.answer_extraction.evidence_invariant import enforce_result_evidence_invariant, validate_extraction_result_evidence
from app.answer_extraction.extraction_engine import extract_answer_key


class AnswerExtractionEvidenceInvariantTests(unittest.TestCase):
    def test_output_with_missing_evidence_is_downgraded(self) -> None:
        result = {
            "status": "accepted",
            "answers": {"1": {"validation_status": "accepted", "source_kind": "answer_table", "source_file": "a.json", "source_span": {"table_id": "t1"}, "evidence_text": ""}},
            "review_items": [],
        }
        fixed = enforce_result_evidence_invariant(result)
        self.assertEqual(fixed["answers"]["1"]["validation_status"], "needs_review")
        self.assertEqual(fixed["status"], "needs_review")

    def test_engine_output_has_no_invariant_violation(self) -> None:
        result = extract_answer_key(["tests/fixtures/answer_extraction/document_models_v3/type2_same_file_itemized_with_real_chinese_brackets.json"]).to_safe_dict()
        self.assertEqual(validate_extraction_result_evidence(result), [])


if __name__ == "__main__":
    unittest.main()
