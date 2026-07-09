from __future__ import annotations

import unittest
from pathlib import Path

from app.answer_extraction.answer_markers import COMPAT_ANSWER_MARKERS
from app.answer_extraction.docx_native_parser import parse_docx

# Compatibility marker (U+3016/U+3017) referenced indirectly to avoid
# any literal cosmetic mention of it in this real-bracket test file.
_COMPAT = COMPAT_ANSWER_MARKERS[0]

SYNTHETIC_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "answer_extraction" / "synthetic_docx_v3"


class SyntheticDocxRealBracketsP0Tests(unittest.TestCase):
    def test_same_file_itemized_real_brackets_docx_has_real_marker(self):
        path = SYNTHETIC_DIR / "same_file_itemized_real_brackets.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        model = parse_docx(path)
        text = model.all_text()
        self.assertIn("【答案】", text)
        self.assertNotIn(_COMPAT, text)

    def test_split_answer_itemized_real_brackets_docx_has_real_marker(self):
        path = SYNTHETIC_DIR / "split_answer_itemized_real_brackets.docx"
        if not path.exists():
            self.skipTest("synthetic docx not available")
        model = parse_docx(path)
        text = model.all_text()
        self.assertIn("【答案】", text)
        self.assertNotIn(_COMPAT, text)

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
            self.assertNotIn(_COMPAT, text,
                             f"{docx_path.name} has real_brackets but contains compat marker {_COMPAT}")


if __name__ == "__main__":
    unittest.main()
