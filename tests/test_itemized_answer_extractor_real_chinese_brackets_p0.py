from __future__ import annotations

import unittest

from app.answer_extraction.answer_markers import COMPAT_ANSWER_MARKERS
from app.answer_extraction.document_model import DocumentModel, ParagraphBlock
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers


def _doc(lines):
    return DocumentModel(
        "real_chinese_brackets_p0",
        "real_chinese_brackets_p0.json",
        [
            ParagraphBlock(
                block_id=f"p{i:03d}",
                text=line,
                raw_text=line,
                order_index=i,
                source_file="real_chinese_brackets_p0.json",
            )
            for i, line in enumerate(lines, 1)
        ],
        [],
    )


_COMPAT = COMPAT_ANSWER_MARKERS[0]  # compat marker, never the literal real marker


class ItemizedAnswerExtractorRealChineseBracketsP0Tests(unittest.TestCase):
    def _candidate(self, lines, qno):
        pool = extract_itemized_answers(_doc(lines)).candidate_pool
        return pool.highest_confidence_candidate(qno)

    def test_real_bracket_dot(self):
        c = self._candidate(["1.【答案】B"], 1)
        self.assertIsNotNone(c)
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_fullwidth_dot(self):
        c = self._candidate(["1．【答案】B"], 1)
        self.assertIsNotNone(c)
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_ideographic_comma(self):
        c = self._candidate(["1、【答案】B"], 1)
        self.assertIsNotNone(c)
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_with_spaces(self):
        c = self._candidate(["1. 【答案】 B"], 1)
        self.assertIsNotNone(c)
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_colon(self):
        c = self._candidate(["1．【答案】：C"], 1)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, "C")
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_multi_answer(self):
        c = self._candidate(["9．【答案】BD"], 9)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, "BD")
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_fraction(self):
        c = self._candidate([r"12．【答案】\frac{1}{2}"], 12)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, r"\frac{1}{2}")
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_interval_expr(self):
        c = self._candidate(["13．【答案】x>1"], 13)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, "x>1")
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_bracketed_interval(self):
        c = self._candidate(["14．【答案】[-1,2]"], 14)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, "[-1,2]")
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)

    def test_real_bracket_cross_block(self):
        c = self._candidate(["1.", "【答案】B"], 1)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, "B")
        self.assertIn("【答案】", c.evidence_text)
        self.assertNotIn(_COMPAT, c.evidence_text)


if __name__ == "__main__":
    unittest.main()
