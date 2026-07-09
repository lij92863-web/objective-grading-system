from __future__ import annotations

import unittest

from app.answer_extraction.document_model import DocumentModel, ParagraphBlock
from app.answer_extraction.question_index_builder import build_question_index, QuestionIndex
from app.answer_extraction.text_normalizer import normalize_text


class QuestionIndexCompleteSpansV3Tests(unittest.TestCase):
    def _doc(self, lines, tables=None):
        return DocumentModel("qi_test", "qi.json",
            [ParagraphBlock(block_id=f"p{i:03d}", text=line, raw_text=line, order_index=i,
                            source_file="qi.json") for i, line in enumerate(lines, 1)], tables or [])

    def test_single_question_single_block(self):
        qi = build_question_index(self._doc(["一、单选题", "1. 集合A={1,2}"], []))
        self.assertEqual(len(qi.questions), 1)
        self.assertEqual(qi.questions[0].question_no, 1)

    def test_question_span_covers_option_blocks(self):
        qi = build_question_index(self._doc(["1. 题目", "A. 选项1", "B. 选项2", "2. 第二题"], []))
        self.assertEqual(len(qi.questions), 2)
        self.assertEqual(qi.questions[0].source_span.end_block, "p003")

    def test_section_header_not_in_question(self):
        qi = build_question_index(self._doc(["一、单选题", "1. 题目"], []))
        self.assertEqual(qi.questions[0].section, "一、单选题")

    def test_answer_section_stops_scan(self):
        qi = build_question_index(self._doc(["1. 题目A", "参考答案", "1. A"]))
        self.assertEqual(len(qi.questions), 1)

    def test_daan_bracket_stops_scan(self):
        qi = build_question_index(self._doc(["1. 题目A", "【答案】", "1. B"]))
        self.assertEqual(len(qi.questions), 1)

    def test_duplicate_question_number_blocked(self):
        qi = build_question_index(self._doc(["1. 题目A", "1. 题目B"]))
        self.assertIn("duplicate_question_number", qi.blocking_errors)

    def test_rewind_question_number_blocked(self):
        qi = build_question_index(self._doc(["5. 题目E", "3. 题目C"]))
        self.assertIn("question_number_rewind", qi.blocking_errors)

    def test_year_line_skipped(self):
        qi = build_question_index(self._doc(["2024年高考数学", "1. 题目"]))
        self.assertEqual(len(qi.questions), 1)

    def test_option_labels_detected(self):
        qi = build_question_index(self._doc(["1. 题目", "A. 选项1", "B. 选项2"]))
        self.assertTrue(qi.questions[0].has_options)
        self.assertIn("A", qi.questions[0].option_labels)

    def test_section_type_inference(self):
        qi = build_question_index(self._doc(["一、单项选择题", "1. 题目"]))
        self.assertEqual(qi.questions[0].question_type, "single_choice")

    def test_no_section_default_unknown(self):
        qi = build_question_index(self._doc(["1. 题目"]))
        self.assertEqual(qi.questions[0].question_type, "unknown")


if __name__ == "__main__":
    unittest.main()
