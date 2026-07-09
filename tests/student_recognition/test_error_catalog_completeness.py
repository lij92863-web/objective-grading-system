"""SRE1091 (part) — verify every ErrorCode has a complete catalog entry.

Run: python -m unittest discover -s tests/student_recognition
"""

import unittest
from pathlib import Path

from app.student_recognition.errors.error_catalog import CATALOG, CatalogEntry
from app.student_recognition.errors.error_codes import ErrorCode

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_SR_DIR = PROJECT_ROOT / "app" / "student_recognition"


class TestErrorCatalogCompleteness(unittest.TestCase):
    def test_every_code_has_catalog_entry(self):
        missing = [c.name for c in ErrorCode if c not in CATALOG]
        self.assertEqual(missing, [], f"ErrorCodes missing catalog entry: {missing}")

    def test_catalog_has_no_extra_codes(self):
        extra = [c.name for c in CATALOG if c not in ErrorCode]
        self.assertEqual(extra, [], f"Catalog entries for unknown codes: {extra}")

    def test_entry_fields_present_and_typed(self):
        for code, entry in CATALOG.items():
            self.assertIsInstance(entry, CatalogEntry, f"{code} entry type")
            self.assertEqual(entry.code, code, f"{code}: code field mismatch")
            self.assertIsInstance(entry.category, str)
            self.assertNotEqual(entry.category.strip(), "", f"{code}: empty category")
            self.assertIsInstance(entry.default_message, str)
            self.assertNotEqual(
                entry.default_message.strip(), "", f"{code}: empty default_message"
            )
            self.assertIsInstance(entry.blocking, bool, f"{code}: blocking not bool")
            self.assertIsInstance(
                entry.requires_review, bool, f"{code}: requires_review not bool"
            )
            self.assertIsInstance(
                entry.can_teacher_override, bool, f"{code}: can_teacher_override not bool"
            )
            self.assertIn(
                entry.severity, {"blocking", "review", "warning"}, f"{code}: bad severity"
            )

    def test_blocking_and_review_flags_consistent_with_severity(self):
        for code, entry in CATALOG.items():
            if entry.severity == "blocking":
                self.assertTrue(entry.blocking, f"{code}: blocking severity but not blocking")
            if entry.severity == "review":
                self.assertTrue(
                    entry.requires_review, f"{code}: review severity but not requires_review"
                )


if __name__ == "__main__":
    unittest.main()
