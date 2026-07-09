from __future__ import annotations

import unittest

from app.answer_extraction.document_model import DocumentModel, ParagraphBlock
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers
from app.answer_extraction.itemized_block_segmenter import segment_itemized_blocks, AnswerItemBlock


class ItemizedAnswerContextV3Tests(unittest.TestCase):
    def _doc(self, lines):
        return DocumentModel("ctx_test", "ctx.json",
            [ParagraphBlock(block_id=f"p{i:03d}", text=line, raw_text=line, order_index=i,
                            source_file="ctx.json") for i, line in enumerate(lines, 1)], [])

    def test_qno_only_line_followed_by_answer(self):
        pool = extract_itemized_answers(self._doc(["1.", "【答案】B", "2.", "【答案】C"])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "B")
        self.assertEqual(pool.highest_confidence_candidate(2).normalized_answer, "C")

    def test_qno_only_with_colon_bracket(self):
        pool = extract_itemized_answers(self._doc(["1.", "【答案】：D"])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "D")

    def test_guxuan_within_segment(self):
        pool = extract_itemized_answers(self._doc(["1. 故选B", "2. 故选C"])).candidate_pool
        self.assertIsNotNone(pool.highest_confidence_candidate(1))

    def test_explicit_bracket_vs_guxuan_conflict(self):
        pool = extract_itemized_answers(self._doc(["1.【答案】C", "2. 故选D"])).candidate_pool
        self.assertIsNotNone(pool.highest_confidence_candidate(1))

    def test_no_trigger_no_candidate(self):
        pool = extract_itemized_answers(self._doc(["1. 这是题目内容，没有答案"])).candidate_pool
        self.assertEqual(pool.question_numbers(), [])

    def test_segment_spans_multiple_paragraphs(self):
        blocks = [ParagraphBlock(block_id=f"p{i:03d}", text=t, raw_text=t, order_index=i, source_file="f.json")
                  for i, t in enumerate(["1. 题目第一段", "题目第二段", "2. B", "故选C"], 1)]
        segments = segment_itemized_blocks(blocks)
        self.assertTrue(len(segments) >= 1)

    def test_parser_after_answer_also_captured(self):
        pool = extract_itemized_answers(self._doc(["1.", "【答案】B", "【解析】本题考察..."])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "B")

    def test_gu_daanwei_in_segment(self):
        pool = extract_itemized_answers(self._doc(["1. 故答案为：x>1", "2. 题目"])).candidate_pool
        self.assertIsNotNone(pool.highest_confidence_candidate(1))

    def test_circled_numbers_not_question(self):
        pool = extract_itemized_answers(self._doc(["① 步骤一", "② 步骤二"])).candidate_pool
        self.assertEqual(pool.question_numbers(), [])

    def test_year_not_question(self):
        pool = extract_itemized_answers(self._doc(["2024年高考真题"])).candidate_pool
        self.assertEqual(pool.question_numbers(), [])


if __name__ == "__main__":
    unittest.main()
