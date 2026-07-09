from __future__ import annotations

import unittest
from pathlib import Path

from app.answer_extraction.docx_native_parser import parse_docx


SYNTHETIC_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "answer_extraction" / "synthetic_docx_v3"


class SyntheticDocxRealBracketsP0Tests(unittest.TestCase):
    def test_same_file_itemized_real_brackets_docx_has_real_marker(self):
        path = SYNTHETIC_DIR / "same_file_itemized_real_brackets.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        model = parse_docx(path)
        text = model.all_text()
        self.assertIn("【答案】", text)
        self.assertNotIn("〖答案〗", text)

    def test_split_answer_itemized_real_brackets_docx_has_real_marker(self):
        path = SYNTHETIC_DIR / "split_answer_itemized_real_brackets.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        model = parse_docx(path)
        text = model.all_text()
        self.assertIn("【答案】", text)
        self.assertNotIn("〖答案〗", text)

    def test_itemized_fill_blank_complex_has_real_brackets(self):
        path = SYNTHETIC_DIR / "itemized_fill_blank_complex.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        model = parse_docx(path)
        text = model.all_text()
        self.assertIn("【答案】", text)

    def test_no_compat_brackets_in_real_bracket_files(self):
        for docx_path in SYNTHETIC_DIR.glob("*real_brackets*.docx"):
            model = parse_docx(docx_path)
            text = model.all_text()
            self.assertNotIn("〖答案〗", text,
                             f"{docx_path.name} has real_brackets but contains compat marker 〖答案〗")


if __name__ == "__main__":
    unittest.main()
