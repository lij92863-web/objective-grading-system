from __future__ import annotations

import ast
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "app" / "answer_extraction"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class StatusModelGuardTests(unittest.TestCase):
    def test_status_model_exists_and_exports_constants(self):
        from app.answer_extraction.status_model import (
            STATUS_ACCEPTED, STATUS_ACCEPTED_WITH_WARNINGS,
            STATUS_NEEDS_REVIEW, STATUS_BLOCKED, STATUS_FAILED,
            FINAL_ACCEPTED_STATUSES, is_final_accepted_status,
        )
        self.assertEqual(STATUS_ACCEPTED, "accepted")
        self.assertIn(STATUS_ACCEPTED, FINAL_ACCEPTED_STATUSES)
        self.assertIn(STATUS_ACCEPTED_WITH_WARNINGS, FINAL_ACCEPTED_STATUSES)
        self.assertTrue(is_final_accepted_status("accepted"))
        self.assertFalse(is_final_accepted_status("needs_review"))

    def test_validator_uses_status_model(self):
        text = _read(APP_ROOT / "answer_key_validator.py")
        self.assertIn("from app.answer_extraction.status_model import", text)

    def test_evidence_invariant_uses_status_model(self):
        text = _read(APP_ROOT / "evidence_invariant.py")
        self.assertIn("from app.answer_extraction.status_model import", text)

    def test_no_hardcoded_accepted_set_in_validator(self):
        text = _read(APP_ROOT / "answer_key_validator.py")
        self.assertNotIn('"accepted"', text.split("from app.answer_extraction.status_model import")[-1].split("def ")[0] if  "from app.answer_extraction.status_model import" in text else text)

    def test_status_model_used_in_extraction_engine(self):
        text = _read(APP_ROOT / "extraction_engine.py")
        self.assertIn("status_model", text, "extraction_engine should import status_model")

    def test_answer_markers_imported_by_itemized_extractor(self):
        text = _read(APP_ROOT / "itemized_answer_extractor.py")
        self.assertIn("from app.answer_extraction.answer_markers import", text)
        self.assertIn("ANSWER_MARKER_PATTERN", text)


if __name__ == "__main__":
    unittest.main()
