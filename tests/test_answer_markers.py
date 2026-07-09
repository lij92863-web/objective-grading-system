from __future__ import annotations

import re
import unittest

from app.answer_extraction.answer_markers import (
    ANSWER_MARKER_RE,
    ANSWER_MARKERS,
    COMPAT_ANSWER_MARKERS,
    REAL_CHINESE_ANSWER_MARKER,
    build_answer_marker_regex,
    is_real_chinese_answer_marker,
)


class AnswerMarkersTests(unittest.TestCase):
    def test_real_chinese_answer_marker_is_primary(self):
        self.assertEqual(REAL_CHINESE_ANSWER_MARKER, "【答案】")
        self.assertEqual(ANSWER_MARKERS[0], "【答案】")

    def test_compat_markers_are_not_real(self):
        self.assertIn("〖答案〗", COMPAT_ANSWER_MARKERS)
        self.assertIn("[答案]", COMPAT_ANSWER_MARKERS)
        self.assertNotIn("【答案】", COMPAT_ANSWER_MARKERS)

    def test_answer_marker_regex_matches_real_marker(self):
        pattern = re.compile(build_answer_marker_regex())
        self.assertTrue(pattern.search("1.【答案】B"))
        self.assertTrue(pattern.search("1.〖答案〗B"))
        self.assertTrue(pattern.search("1.[答案]B"))

    def test_build_answer_marker_regex_is_string(self):
        regex = build_answer_marker_regex()
        self.assertIsInstance(regex, str)
        self.assertIn("【答案】", regex)
        self.assertIn("〖答案〗", regex)
        self.assertIn("答案", regex)  # re.escape escapes brackets so we check core chars

    def test_compiled_regex_matches_all_markers(self):
        self.assertTrue(ANSWER_MARKER_RE.search("1.【答案】B"))
        self.assertTrue(ANSWER_MARKER_RE.search("1.〖答案〗C"))
        self.assertTrue(ANSWER_MARKER_RE.search("1.[答案]D"))

    def test_is_real_chinese_answer_marker(self):
        self.assertTrue(is_real_chinese_answer_marker("1.【答案】B"))
        self.assertTrue(is_real_chinese_answer_marker("【答案】C"))
        self.assertFalse(is_real_chinese_answer_marker("1.〖答案〗B"))
        self.assertFalse(is_real_chinese_answer_marker("1.[答案]B"))
        self.assertFalse(is_real_chinese_answer_marker("plain text"))

    def test_answer_markers_count(self):
        self.assertEqual(len(ANSWER_MARKERS), 3)
        self.assertEqual(len(COMPAT_ANSWER_MARKERS), 2)


if __name__ == "__main__":
    unittest.main()
