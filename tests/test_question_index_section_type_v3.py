from __future__ import annotations

import unittest

from app.answer_extraction.question_index_builder import _question_type_from_section


class QuestionIndexSectionTypeV3Tests(unittest.TestCase):
    def test_single_choice_variants(self):
        for section in ["一、单选题", "二、单项选择题", "三、单项选择"]:
            with self.subTest(section=section):
                self.assertEqual(_question_type_from_section(section), "single_choice")

    def test_multi_choice_variants(self):
        for section in ["二、多选题", "一、多项选择题", "三、多项选择"]:
            with self.subTest(section=section):
                self.assertEqual(_question_type_from_section(section), "multi_choice")

    def test_blank(self):
        self.assertEqual(_question_type_from_section("三、填空题"), "blank")

    def test_solution(self):
        self.assertEqual(_question_type_from_section("四、解答题"), "solution")

    def test_unknown_for_unrecognized(self):
        self.assertEqual(_question_type_from_section("五、综合题"), "unknown")

    def test_empty_string_returns_unknown(self):
        self.assertEqual(_question_type_from_section(""), "unknown")

    def test_partial_match(self):
        self.assertEqual(_question_type_from_section("第I卷 单项选择题部分"), "single_choice")

    def test_multiple_keywords_picks_first_match(self):
        self.assertEqual(_question_type_from_section("单选题和多选题混合"), "single_choice")


if __name__ == "__main__":
    unittest.main()
