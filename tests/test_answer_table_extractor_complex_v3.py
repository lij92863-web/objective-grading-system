from __future__ import annotations

import unittest

from app.answer_extraction.answer_table_extractor import extract_answer_tables
from app.answer_extraction.document_model import DocumentCell, DocumentModel, DocumentTable, TableBlock


def _table(table_id, rows_data, source_file="f.json"):
    cells = []
    for ri, row in enumerate(rows_data):
        for ci, val in enumerate(row):
            cells.append(DocumentCell(row_index=ri, col_index=ci, text=val, raw_text=val))
    return DocumentTable(table_id=table_id, cells=cells, row_count=len(rows_data),
                         col_count=max(len(r) for r in rows_data) if rows_data else 0,
                         source_file=source_file)


class AnswerTableExtractorComplexV3Tests(unittest.TestCase):
    def _doc(self, tables, source_file="f.json"):
        blocks = []
        for t in tables:
            tb = TableBlock.from_table(t, block_id=f"tb_{t.table_id}")
            tb.source_file = source_file
            blocks.append(tb)
        return DocumentModel("test", source_file, blocks, tables)

    def test_horizontal_row_pair(self):
        t = _table("t1", [["题号", "1", "2", "3"], ["答案", "A", "B", "C"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "A")
        self.assertEqual(pool.highest_confidence_candidate(2).normalized_answer, "B")
        self.assertEqual(pool.highest_confidence_candidate(3).normalized_answer, "C")

    def test_vertical_columns(self):
        t = _table("t1", [["题号", "答案"], ["1", "A"], ["2", "B"], ["3", "CD"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "A")
        self.assertEqual(pool.highest_confidence_candidate(3).normalized_answer, "CD")

    def test_multi_table_answers(self):
        t1 = _table("t1", [["题号", "1", "2"], ["答案", "A", "B"]])
        t2 = _table("t2", [["题号", "3", "4"], ["答案", "C", "D"]])
        pool = extract_answer_tables(self._doc([t1, t2])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "A")
        self.assertEqual(pool.highest_confidence_candidate(3).normalized_answer, "C")
        self.assertEqual(pool.highest_confidence_candidate(4).normalized_answer, "D")

    def test_empty_rows_between(self):
        t = _table("t1", [["题号", "1", "2"], ["", "", ""], ["答案", "B", "C"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "B")

    def test_two_digit_question_numbers(self):
        t = _table("t1", [["题号", "10", "11", "12"], ["答案", "A", "BD", "C"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(10).normalized_answer, "A")
        self.assertEqual(pool.highest_confidence_candidate(12).normalized_answer, "C")

    def test_multi_select_answers(self):
        t = _table("t1", [["题号", "1", "2"], ["答案", "B D", "B、D"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "BD")

    def test_chinese_header_labels(self):
        t = _table("t1", [["题号", "1", "2"], ["答案", "A", "B"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "A")

    def test_blank_answer_expression(self):
        t = _table("t1", [["题号", "1", "2"], ["答案", "x>1", "[-1,2]"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        c1 = pool.highest_confidence_candidate(1)
        c2 = pool.highest_confidence_candidate(2)
        self.assertIsNotNone(c1)
        self.assertIsNotNone(c2)
        actual_1 = c1.normalized_answer.upper() if c1.normalized_answer else c1.raw_answer
        actual_2 = c2.normalized_answer.upper() if c2.normalized_answer else c2.raw_answer
        self.assertIn(actual_1, ("X>1", ">1", "x>1"))
        self.assertIn(actual_2, ("[-1,2]", "[1,2]", "[-12]"))

    def test_segmented_row_pairs(self):
        t = _table("t1", [["题号", "1", "2"], ["答案", "A", "B"],
                           ["题号", "3", "4"], ["答案", "C", "D"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "A")
        self.assertEqual(pool.highest_confidence_candidate(3).normalized_answer, "C")

    def test_empty_answer_cells_skipped(self):
        t = _table("t1", [["题号", "1", "2"], ["答案", "A", ""]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        self.assertIsNotNone(pool.highest_confidence_candidate(1))
        self.assertIsNone(pool.highest_confidence_candidate(2))

    def test_evidence_text_present(self):
        t = _table("t1", [["题号", "1"], ["答案", "B"]])
        pool = extract_answer_tables(self._doc([t])).candidate_pool
        c = pool.highest_confidence_candidate(1)
        self.assertTrue(c.evidence_text)


if __name__ == "__main__":
    unittest.main()
