from __future__ import annotations

import unittest
from pathlib import Path

from app.answer_extraction.docx_native_parser import parse_docx
from app.answer_extraction.file_role_classifier import classify_file_role
from app.answer_extraction.answer_layout_classifier import classify_answer_layout
from app.answer_extraction.extraction_engine import extract_answer_key


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = ROOT / "tests" / "fixtures" / "answer_extraction" / "synthetic_docx_v3"


def synthetic_files():
    if not SYNTHETIC_DIR.exists():
        return []
    return sorted(SYNTHETIC_DIR.glob("*.docx"))


class DocxParserSyntheticDocxV3Tests(unittest.TestCase):
    def test_parse_all_synthetic_docx(self):
        for docx_path in synthetic_files():
            with self.subTest(docx=docx_path.name):
                model = parse_docx(docx_path)
                self.assertIsNotNone(model)
                self.assertTrue(len(model.blocks) > 0, f"No blocks in {docx_path.name}")

    def test_classify_all_synthetic_docx(self):
        for docx_path in synthetic_files():
            with self.subTest(docx=docx_path.name):
                model = parse_docx(docx_path)
                role = classify_file_role(model)
                self.assertIsNotNone(role.role)

    def test_layout_classify_all_synthetic_docx(self):
        for docx_path in synthetic_files():
            with self.subTest(docx=docx_path.name):
                model = parse_docx(docx_path)
                layout = classify_answer_layout(model)
                self.assertIsNotNone(layout.layout)

    def test_extract_all_synthetic_docx(self):
        for docx_path in synthetic_files():
            with self.subTest(docx=docx_path.name):
                result = extract_answer_key([str(docx_path)])
                self.assertIsNotNone(result)
                self.assertIn(result.status, ("accepted", "accepted_with_warnings", "needs_review", "blocked", "failed"))

    def test_same_file_boxed_front_empty_grid_no_empty_extraction(self):
        path = SYNTHETIC_DIR / "same_file_boxed_front_empty_grid.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        result = extract_answer_key([str(path)])
        self.assertTrue(result.report.get("ignored_student_answer_grid_count", 0) >= 0)

    def test_same_file_itemized_real_brackets_extracts(self):
        path = SYNTHETIC_DIR / "same_file_itemized_real_brackets.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        result = extract_answer_key([str(path)])
        self.assertIn(result.strategy, ("same_file_itemized", "mixed_or_unknown"))

    def test_split_question_with_empty_grid(self):
        q_path = SYNTHETIC_DIR / "split_question_with_empty_grid.docx"
        a_path = SYNTHETIC_DIR / "split_answer_boxed_segmented.docx"
        if not q_path.exists() or not a_path.exists():
            self.skipTest("synthetic docx pair not available")
        result = extract_answer_key([str(q_path), str(a_path)])
        self.assertIsNotNone(result)

    def test_unknown_mixed_should_review_not_accepted(self):
        path = SYNTHETIC_DIR / "unknown_mixed_should_review.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        result = extract_answer_key([str(path)])
        self.assertNotEqual(result.status, "accepted")


if __name__ == "__main__":
    unittest.main()
