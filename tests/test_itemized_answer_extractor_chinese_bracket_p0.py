from __future__ import annotations

import unittest

from app.answer_extraction.document_model import DocumentModel, ParagraphBlock
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers


def doc(lines: list[str]) -> DocumentModel:
    return DocumentModel(
        "bracket_p0",
        "bracket_p0.json",
        [ParagraphBlock(block_id=f"p{i:03d}", text=line, raw_text=line, order_index=i, source_file="bracket_p0.json") for i, line in enumerate(lines, 1)],
        [],
    )


class ItemizedChineseBracketP0Tests(unittest.TestCase):
    def answer(self, lines: list[str], question_no: int = 1) -> str:
        pool = extract_itemized_answers(doc(lines)).candidate_pool
        candidate = pool.highest_confidence_candidate(question_no)
        self.assertIsNotNone(candidate)
        self.assertIn("【答案】", candidate.evidence_text)
        return candidate.normalized_answer

    def test_direct_real_bracket_patterns(self) -> None:
        cases = [
            (["1.【答案】B"], 1, "B"),
            (["1．【答案】B"], 1, "B"),
            (["1、【答案】B"], 1, "B"),
            (["1. 【答案】 B"], 1, "B"),
            (["9．【答案】BD"], 9, "BD"),
            (["12．【答案】\\frac{1}{2}"], 12, "\\frac{1}{2}"),
            (["13．【答案】x>1"], 13, "x>1"),
            (["14．【答案】[-1,2]"], 14, "[-1,2]"),
            (["1.", "【答案】B"], 1, "B"),
            (["1.", "【答案】：B"], 1, "B"),
            (["1.", "【答案】BD"], 1, "BD"),
        ]
        for lines, question_no, expected in cases:
            with self.subTest(lines=lines):
                self.assertEqual(self.answer(lines, question_no), expected)

    def test_other_answer_tokens_still_work(self) -> None:
        pool = extract_itemized_answers(doc(["1.〖答案〗B", "2.[答案]C", "3.故选：D", "4.故答案为：A"])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "B")
        self.assertEqual(pool.highest_confidence_candidate(2).normalized_answer, "C")
        self.assertEqual(pool.highest_confidence_candidate(3).normalized_answer, "D")
        self.assertEqual(pool.highest_confidence_candidate(4).normalized_answer, "A")

    def test_no_question_number_does_not_invent_id(self) -> None:
        pool = extract_itemized_answers(doc(["【答案】B"])).candidate_pool
        self.assertEqual(pool.question_numbers(), [])


if __name__ == "__main__":
    unittest.main()
