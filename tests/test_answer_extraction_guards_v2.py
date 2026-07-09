from __future__ import annotations

import unittest
from pathlib import Path

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_key_validator import validate_answer_key
from app.answer_extraction.cross_file_aligner import align_by_question_no
from app.answer_extraction.extraction_engine import extract_answer_key, load_document
from app.answer_extraction.question_index_builder import build_question_index


ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "tests" / "fixtures" / "answer_extraction" / "document_models_v2"
SCANNED = [
    ROOT / "app" / "answer_extraction",
    ROOT / "scripts" / "extract_answer_key.py",
    ROOT / "scripts" / "classify_paper_files.py",
    ROOT / "scripts" / "run_local_answer_extraction_smoke.py",
]


class AnswerExtractionGuardsV2Tests(unittest.TestCase):
    def test_accepted_answers_have_evidence(self) -> None:
        result = extract_answer_key([str(V2 / "type1_same_file_boxed_realistic.json")]).to_safe_dict()
        for answer in result["answers"].values():
            if answer["validation_status"] == "accepted":
                self.assertTrue(answer["evidence_text"])
                self.assertTrue(answer["source_kind"])
                self.assertTrue(answer["source_file"] or answer["source_span"])

    def test_llm_candidate_never_accepted(self) -> None:
        question_index = build_question_index(load_document(V2 / "type1_same_file_boxed_realistic.json"))
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(1, "B", "B", source_kind="llm_candidate", evidence_text="1.【答案】B", confidence=0.7))
        report = validate_answer_key(question_index, pool, align_by_question_no(question_index, pool))
        self.assertNotEqual(report.answer_statuses.get(1), "accepted")

    def test_missing_answer_not_guessed(self) -> None:
        result = extract_answer_key([str(V2 / "mixed_unknown_should_review.json")]).to_safe_dict()
        self.assertEqual(result["answer_count"], 0)

    def test_no_forbidden_report_or_grading_terms(self) -> None:
        chunks = []
        for path in SCANNED:
            if path.is_dir():
                chunks.extend(file.read_text(encoding="utf-8") for file in path.rglob("*.py"))
            else:
                chunks.append(path.read_text(encoding="utf-8"))
        text = "\n".join(chunks)
        for token in ["grade_all", "objective_grader", "workflow", ".csv", ".xlsx", ".html", "Authorization", "Bearer", "QWEN_API_KEY"]:
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
