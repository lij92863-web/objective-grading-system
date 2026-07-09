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


def _tb(table, order=None):
    tb = TableBlock.from_table(table, f"tb_{table.table_id}")
    tb.source_file = table.source_file
    if order is not None:
        tb.order_index = order
    return tb


class StudentGridP0GuardV3Tests(unittest.TestCase):
    def test_front_empty_grid_never_yields_answer(self):
        t = _table("t_front", [["题号", "1", "2", "3"], ["答案", "", "", ""]])
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：____ 姓名：____", order_index=0, source_file="f.json"),
            _tb(t),
        ], [t])
        pool = extract_answer_tables(doc).candidate_pool
        self.assertEqual(pool.question_numbers(), [])

    def test_nearly_empty_grid_never_yields_answer(self):
        t = _table("t1", [["题号", "1", "2", "3", "4", "5", "6"], ["答案", "A", "", "", "", "", ""]])
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：____", order_index=0, source_file="f.json"),
            _tb(t),
        ], [t])
        pool = extract_answer_tables(doc).candidate_pool
        self.assertEqual(pool.question_numbers(), [])

    def test_grid_with_class_name_fields_ignored(self):
        t = _table("t1", [["题号", "1", "2"], ["答案", "", ""]])
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：高二3班 姓名：____ 考号：____", order_index=0, source_file="f.json"),
            _tb(t),
        ], [t])
        detection = detect_student_answer_grid(t, doc)
        self.assertTrue(detection.is_student_answer_grid)

    def test_ignored_grid_count_appears_in_result(self):
        grid = _table("t_grid", [["题号", "1", "2"], ["答案", "", ""]])
        ans = _table("t_ans", [["题号", "3"], ["答案", "C"]])
        ans.order_index = 3
        grid_tb = _tb(grid, order=1)
        ans_tb = _tb(ans, order=3)
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "姓名：____", order_index=0, source_file="f.json"),
            grid_tb,
            ParagraphBlock("p002", "paragraph", "参考答案", order_index=2, source_file="f.json"),
            ans_tb,
        ], [grid, ans])
        result = extract_answer_tables(doc)
        self.assertGreaterEqual(len(result.ignored_tables), 0)

    def test_later_real_answer_table_still_extracted(self):
        grid = _table("t_grid", [["题号", "1", "2"], ["答案", "", ""]])
        ans = _table("t_ans", [["题号", "1", "2"], ["答案", "A", "B"]])
        ans.order_index = 5
        grid_tb = _tb(grid, order=1)
        ans_tb = _tb(ans, order=5)
        doc = DocumentModel("test", "f.json", [
            ParagraphBlock("p001", "paragraph", "班级：____", order_index=0, source_file="f.json"),
            grid_tb,
            ParagraphBlock("p002", "paragraph", "一、单选题", order_index=2, source_file="f.json"),
            ParagraphBlock("p003", "paragraph", "1. 题目", order_index=3, source_file="f.json"),
            ParagraphBlock("p004", "paragraph", "参考答案", order_index=4, source_file="f.json"),
            ans_tb,
        ], [grid, ans])
        pool = extract_answer_tables(doc).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(1).normalized_answer, "A")
        self.assertEqual(pool.highest_confidence_candidate(2).normalized_answer, "B")


if __name__ == "__main__":
    unittest.main()
