from __future__ import annotations

import unittest

from app.answer_extraction.fill_blank_answer_classifier import FillBlankAnswerDecision, classify_fill_blank_answer


class FillBlankAnswerHandlingV3Tests(unittest.TestCase):
    def test_pure_choice_needs_review(self):
        for letter in ("A", "B", "C", "D"):
            with self.subTest(letter=letter):
                result = classify_fill_blank_answer(letter)
                self.assertTrue(result.needs_review)
                self.assertEqual(result.warning, "blank_pure_choice_review")
                self.assertEqual(result.normalized_answer, letter)

    def test_math_expression_no_review(self):
        expressions = [
            r"\frac{1}{2}", "1/2", "0.5", "x>1", "[-1,2]",
            r"(-\infty,1)", r"\sqrt{3}", "π/6", "{1,2,3}",
        ]
        for expr in expressions:
            with self.subTest(expr=expr):
                result = classify_fill_blank_answer(expr)
                self.assertFalse(result.needs_review)
                self.assertEqual(result.warning, "fill_answer_low_confidence")

    def test_multi_letter_not_pure_choice(self):
        result = classify_fill_blank_answer("BD")
        self.assertEqual(result.normalized_answer, "BD")
        self.assertNotEqual(result.normalized_answer, "A")
        self.assertNotEqual(result.normalized_answer, "B")
        self.assertNotEqual(result.normalized_answer, "C")
        self.assertNotEqual(result.normalized_answer, "D")

    def test_empty_answer(self):
        result = classify_fill_blank_answer("")
        self.assertFalse(result.needs_review)

    def test_lowercase_choice_not_detected_as_pure_choice(self):
        result = classify_fill_blank_answer("a")
        self.assertFalse(result.needs_review)
        self.assertEqual(result.normalized_answer, "a")

    def test_numeric_answer(self):
        result = classify_fill_blank_answer("3.14")
        self.assertFalse(result.needs_review)

    def test_chinese_text_not_choice(self):
        result = classify_fill_blank_answer("正确")
        self.assertFalse(result.needs_review)

    def test_negative_number(self):
        result = classify_fill_blank_answer("-5")
        self.assertFalse(result.needs_review)

    def test_fraction_with_slash(self):
        result = classify_fill_blank_answer("3/4")
        self.assertFalse(result.needs_review)

    def test_set_notation(self):
        result = classify_fill_blank_answer("{x|x>1}")
        self.assertFalse(result.needs_review)


if __name__ == "__main__":
    unittest.main()
