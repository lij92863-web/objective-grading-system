from __future__ import annotations

import unittest

from app.answer_extraction.extraction_engine import extract_answer_key


class AnswerExtractionV3ChineseBracketFixturesTests(unittest.TestCase):
    def test_same_file_real_chinese_brackets(self) -> None:
        result = extract_answer_key(["tests/fixtures/answer_extraction/document_models_v3/type2_same_file_itemized_with_real_chinese_brackets.json"]).to_safe_dict()
        self.assertEqual(result["strategy"], "same_file_itemized")
        self.assertEqual(result["answers"]["1"]["answer"], "B")
        self.assertIn("【答案】", result["answers"]["1"]["evidence_text"])

    def test_fill_blank_real_chinese_brackets(self) -> None:
        result = extract_answer_key(["tests/fixtures/answer_extraction/document_models_v3/type2_same_file_itemized_fill_blank_real_brackets.json"]).to_safe_dict()
        self.assertEqual(result["status"], "accepted_with_warnings")
        self.assertEqual(result["answers"]["12"]["answer"], "\\frac{1}{2}")
        self.assertIn("【答案】", result["answers"]["12"]["evidence_text"])

    def test_split_itemized_real_chinese_brackets(self) -> None:
        result = extract_answer_key([
            "tests/fixtures/answer_extraction/document_models_v3/type4_question_with_empty_grid_realistic.json",
            "tests/fixtures/answer_extraction/document_models_v3/type4_answer_itemized_real_chinese_brackets.json",
        ]).to_safe_dict()
        self.assertEqual(result["strategy"], "split_file_itemized")
        self.assertEqual(result["answers"]["1"]["answer"], "B")


if __name__ == "__main__":
    unittest.main()
