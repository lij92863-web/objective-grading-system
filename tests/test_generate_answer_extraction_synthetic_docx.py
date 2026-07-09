from __future__ import annotations

import unittest

from app.answer_extraction.docx_native_parser import parse_docx
from scripts.generate_answer_extraction_synthetic_docx import OUT_DIR, generate


class GenerateAnswerExtractionSyntheticDocxTests(unittest.TestCase):
    def test_generate_and_parse_docx(self) -> None:
        result = generate()
        self.assertEqual(result["count"], 8)
        for docx in OUT_DIR.glob("*.docx"):
            with self.subTest(docx=docx.name):
                document = parse_docx(docx)
                self.assertTrue(document.sorted_blocks())


if __name__ == "__main__":
    unittest.main()
