from __future__ import annotations

import ast
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "app" / "answer_extraction"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class AnswerSourcePolicyUsageGuardTests(unittest.TestCase):
    def test_itemized_extractor_imports_confidence_for_source(self):
        text = _read(APP_ROOT / "itemized_answer_extractor.py")
        self.assertIn("from app.answer_extraction.answer_source_policy import confidence_for_source", text)

    def test_itemized_extractor_uses_confidence_for_source(self):
        text = _read(APP_ROOT / "itemized_answer_extractor.py")
        # The confidence_for_source function must be called in the extractor
        self.assertIn("confidence_for_source(", text)

    def test_source_policy_defines_explicit_bracket_answer(self):
        from app.answer_extraction.answer_source_policy import CONFIDENCE_BY_SOURCE
        self.assertIn("explicit_bracket_answer", CONFIDENCE_BY_SOURCE)
        self.assertGreater(CONFIDENCE_BY_SOURCE["explicit_bracket_answer"], 0.95)

    def test_confidence_from_policy_matches_expected(self):
        from app.answer_extraction.answer_source_policy import confidence_for_source
        self.assertEqual(confidence_for_source("explicit_bracket_answer"), 0.98)
        self.assertEqual(confidence_for_source("answer_table"), 0.99)

    def test_no_hardcoded_confidence_in_bracket_path(self):
        text = _read(APP_ROOT / "itemized_answer_extractor.py")
        self.assertIn("confidence_for_source", text,
                      "itemized_answer_extractor should use confidence_for_source, not magic numbers")

    def test_evidence_text_preserved_in_source_policy(self):
        from app.answer_extraction.answer_source_policy import CONFIDENCE_BY_SOURCE
        self.assertIsInstance(CONFIDENCE_BY_SOURCE, dict)
        self.assertTrue(all(isinstance(v, float) for v in CONFIDENCE_BY_SOURCE.values()))


if __name__ == "__main__":
    unittest.main()
