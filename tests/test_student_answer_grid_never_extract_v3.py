from __future__ import annotations

import unittest

from app.answer_extraction.answer_table_extractor import extract_answer_tables
from app.answer_extraction.document_model import DocumentCell, DocumentModel, DocumentTable, TableBlock, ParagraphBlock
from app.answer_extraction.student_answer_grid_detector import detect_student_answer_grid


def _table(table_id, rows_data, source_file="f.json"):
    cells = []
    for ri, row in enumerate(rows_data):
        for ci, val in enumerate(row):
            cells.append(DocumentCell(row_index=ri, col_index=ci, text=val, raw_text=val))
    return DocumentTable(table_id=table_id, cells=cells, row_count=len(rows_data),
                         col_count=max(len(r) for r in rows_data) if rows_data else 0, source_file=source_file)


def _tb(table, block_id=None):
    tb = TableBlock.from_table(table, block_id or f"tb_{table.table_id}")
    tb.source_file = table.source_file
    tb.order_index = table.order_index
    return tb


class StudentAnswerGridNeverExtractV3Tests(unittest.TestCase):
    def test_empty_answer_row_detected_as_grid(self):
        t = _table("t1", [["题号", "1", "2", "3"], ["答案", "", "", ""]])
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：____ 姓名：____", order_index=0, source_file="f.json"),
            _tb(t),
        ], [t])
        detection = detect_student_answer_grid(t, doc)
        self.assertTrue(detection.is_student_answer_grid)

    def test_nearly_empty_answer_row_detected(self):
        t = _table("t1", [["题号", "1", "2", "3", "4", "5", "6"], ["答案", "A", "", "", "", "", ""]])
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：____", order_index=0, source_file="f.json"),
            _tb(t),
        ], [t])
        detection = detect_student_answer_grid(t, doc)
        self.assertTrue(detection.is_student_answer_grid)

    def test_front_grid_ignored_later_table_extracted(self):
        grid = _table("t_grid", [["题号", "1", "2"], ["答案", "", ""]])
        answer_t = _table("t_ans", [["题号", "1", "2"], ["答案", "A", "B"]])
        answer_t.order_index = 4
        grid_tb = _tb(grid)
        grid_tb.order_index = 1
        ans_tb = _tb(answer_t)
        ans_tb.order_index = 4
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：____", order_index=0, source_file="f.json"),
            grid_tb,
            ParagraphBlock("p002", "paragraph", "一、单选题", order_index=2, source_file="f.json"),
            ParagraphBlock("p003", "paragraph", "1. 题目", order_index=3, source_file="f.json"),
            ans_tb,
        ], [grid, answer_t])
        result = extract_answer_tables(doc)
        self.assertIn("t_grid", result.ignored_tables)
        self.assertTrue(result.candidate_pool.highest_confidence_candidate(1) is not None)

    def test_grid_alone_produces_no_candidates(self):
        t = _table("t1", [["题号", "1", "2"], ["答案", "", ""]])
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：____", order_index=0, source_file="f.json"),
            _tb(t),
        ], [t])
        pool = extract_answer_tables(doc).candidate_pool
        self.assertEqual(pool.question_numbers(), [])

    def test_full_answer_table_not_flagged_as_grid(self):
        t = _table("t1", [["题号", "1", "2", "3"], ["答案", "A", "B", "C"]])
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p002", "paragraph", "参考答案", order_index=0, source_file="f.json"),
            _tb(t),
        ], [t])
        detection = detect_student_answer_grid(t, doc)
        self.assertFalse(detection.is_student_answer_grid)


if __name__ == "__main__":
    unittest.main()
