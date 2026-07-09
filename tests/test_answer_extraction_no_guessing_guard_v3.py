from __future__ import annotations

import unittest

from app.answer_extraction.document_model import DocumentModel, ParagraphBlock
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers
from app.answer_extraction.answer_table_extractor import extract_answer_tables
from app.answer_extraction.llm_fallback_extractor import LlmFallbackExtractor, LlmFallbackConfig


class NoGuessingGuardV3Tests(unittest.TestCase):
    def test_missing_answer_not_auto_filled(self):
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "1. 题目内容", order_index=0, source_file="f.json"),
        ], [])
        pool = extract_itemized_answers(doc).candidate_pool
        self.assertIsNone(pool.highest_confidence_candidate(1))

    def test_answer_gap_not_backfilled(self):
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "1.【答案】A", order_index=0, source_file="f.json"),
            ParagraphBlock("p002", "paragraph", "3.【答案】C", order_index=1, source_file="f.json"),
        ], [])
        pool = extract_itemized_answers(doc).candidate_pool
        self.assertIsNotNone(pool.highest_confidence_candidate(1))
        self.assertIsNone(pool.highest_confidence_candidate(2))
        self.assertIsNotNone(pool.highest_confidence_candidate(3))

    def test_no_trigger_no_answer(self):
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "1. 这是题目不是答案", order_index=0, source_file="f.json"),
        ], [])
        pool = extract_itemized_answers(doc).candidate_pool
        self.assertEqual(pool.question_numbers(), [])

    def test_llm_disabled_returns_none(self):
        extractor = LlmFallbackExtractor(LlmFallbackConfig(enabled=False))
        result = extractor.extract_candidate("snippet", 1, "A", "evidence")
        self.assertIsNone(result)

    def test_llm_candidate_never_auto_accepted_in_validator(self):
        from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
        from app.answer_extraction.answer_key_validator import validate_answer_key
        from app.answer_extraction.question_index_builder import QuestionIndex, QuestionIndexItem
        from app.answer_extraction.cross_file_aligner import AlignmentResult

        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(question_no=1, raw_answer="B", normalized_answer="B",
                                  source_kind="llm_candidate", source_file="f.json",
                                  evidence_text="some ev", confidence=0.70))
        qi = QuestionIndex([QuestionIndexItem(question_no=1, question_type="single_choice")])
        report = validate_answer_key(qi, pool, AlignmentResult())
        self.assertEqual(report.answer_statuses[1], "needs_review")

    def test_question_text_not_treated_as_answer(self):
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "1. 已知函数f(x)=x^2，求f(2)的值", order_index=0, source_file="f.json"),
        ], [])
        pool = extract_itemized_answers(doc).candidate_pool
        self.assertEqual(pool.question_numbers(), [])


if __name__ == "__main__":
    unittest.main()
