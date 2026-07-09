from __future__ import annotations

import unittest

from app.answer_extraction.answer_source_policy import CONFIDENCE_BY_SOURCE, confidence_for_source


class AnswerSourcePolicyV3Tests(unittest.TestCase):
    def test_answer_table_highest_confidence(self):
        self.assertEqual(confidence_for_source("answer_table"), 0.99)

    def test_explicit_bracket_answer_confidence(self):
        self.assertEqual(confidence_for_source("explicit_bracket_answer"), 0.98)

    def test_explicit_answer_confidence(self):
        self.assertEqual(confidence_for_source("explicit_answer"), 0.97)

    def test_explicit_answer_colon_confidence(self):
        self.assertEqual(confidence_for_source("explicit_answer_colon"), 0.96)

    def test_short_itemized_confidence(self):
        self.assertEqual(confidence_for_source("short_itemized"), 0.95)

    def test_guxuan_confidence(self):
        self.assertEqual(confidence_for_source("guxuan"), 0.88)

    def test_gu_daanwei_confidence(self):
        self.assertEqual(confidence_for_source("gu_daanwei"), 0.86)

    def test_llm_candidate_confidence(self):
        self.assertEqual(confidence_for_source("llm_candidate"), 0.70)

    def test_unknown_returns_zero(self):
        self.assertEqual(confidence_for_source("unknown"), 0.0)

    def test_missing_source_returns_zero(self):
        self.assertEqual(confidence_for_source("nonexistent"), 0.0)

    def test_confidence_ordering(self):
        sources = ["answer_table", "explicit_bracket_answer", "explicit_answer",
                    "explicit_answer_colon", "short_itemized", "guxuan",
                    "gu_daanwei", "llm_candidate"]
        for i in range(len(sources) - 1):
            self.assertGreater(
                confidence_for_source(sources[i]),
                confidence_for_source(sources[i + 1]),
                f"{sources[i]} should have higher confidence than {sources[i + 1]}",
            )

    def test_all_known_sources_in_policy(self):
        for source in ["answer_table", "explicit_bracket_answer", "explicit_answer",
                        "explicit_answer_colon", "short_itemized", "guxuan",
                        "gu_daanwei", "llm_candidate", "unknown"]:
            self.assertIn(source, CONFIDENCE_BY_SOURCE)


if __name__ == "__main__":
    unittest.main()
