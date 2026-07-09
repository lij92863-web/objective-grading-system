from __future__ import annotations

import unittest

from app.answer_extraction.document_model import DocumentModel, ParagraphBlock
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers


def _doc(lines):
    return DocumentModel("compat_test", "compat.json",
        [ParagraphBlock(block_id=f"p{i:03d}", text=line, raw_text=line, order_index=i,
                        source_file="compat.json") for i, line in enumerate(lines, 1)], [])


class ItemizedAnswerExtractorCompatBracketsTests(unittest.TestCase):
    def test_compat_double_bracket_still_works(self):
        pool = extract_itemized_answers(_doc(["1.〖答案〗B"])).candidate_pool
        c = pool.highest_confidence_candidate(1)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, "B")
        self.assertIn("〖答案〗", c.evidence_text)

    def test_compat_square_bracket_still_works(self):
        pool = extract_itemized_answers(_doc(["1.[答案]C"])).candidate_pool
        c = pool.highest_confidence_candidate(1)
        self.assertIsNotNone(c)
        self.assertEqual(c.normalized_answer, "C")
        self.assertIn("[答案]", c.evidence_text)

    def test_compat_evidence_preserves_original_marker(self):
        pool = extract_itemized_answers(_doc(["1.〖答案〗D"])).candidate_pool
        c = pool.highest_confidence_candidate(1)
        # Evidence text must preserve the original marker, not normalize it
        self.assertIn("〖答案〗", c.evidence_text)
        self.assertNotIn("【答案】", c.evidence_text)

    def test_compat_file_not_named_real_brackets(self):
        self.assertIn("compat", __file__)

    def test_cross_block_compat_bracket(self):
        pool = extract_itemized_answers(_doc(["1.", "〖答案〗B"])).candidate_pool
        c = pool.highest_confidence_candidate(1)
        self.assertIsNotNone(c)
        self.assertIn("〖答案〗", c.evidence_text)

    def test_source_kind_is_explicit_bracket_answer(self):
        pool = extract_itemized_answers(_doc(["1.〖答案〗A"])).candidate_pool
        c = pool.highest_confidence_candidate(1)
        self.assertEqual(c.source_kind, "explicit_bracket_answer")


if __name__ == "__main__":
    unittest.main()
