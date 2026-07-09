"""Identity contract tests (constitution §8)."""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.identity_contract import (
    check_duplicate_students,
    parse_identity,
    validate_identity,
)


class TestParseIdentity(unittest.TestCase):
    def test_one_li_ming_contract(self):
        c = parse_identity("1李明")
        self.assertEqual(c.student_id, "1")
        self.assertEqual(c.name, "李明")

    def test_name_only(self):
        c = parse_identity("李明")
        self.assertIsNone(c.student_id)
        self.assertEqual(c.name, "李明")

    def test_empty(self):
        c = parse_identity("")
        self.assertIsNone(c.student_id)
        self.assertIsNone(c.name)


class TestValidateIdentity(unittest.TestCase):
    def test_both_missing(self):
        self.assertEqual(validate_identity(None, None, None), [ErrorCode.IDENTITY_MISSING])

    def test_name_only(self):
        self.assertEqual(
            validate_identity(None, "李明", {"1": "李明"}), [ErrorCode.IDENTITY_NAME_ONLY]
        )

    def test_no_roster(self):
        self.assertEqual(
            validate_identity("1", None, None), [ErrorCode.IDENTITY_ROSTER_NOT_FOUND]
        )

    def test_unmatched_id(self):
        self.assertEqual(
            validate_identity("9", None, {"1": "李明"}), [ErrorCode.IDENTITY_STUDENT_ID_ONLY_UNMATCHED]
        )

    def test_conflict(self):
        self.assertEqual(
            validate_identity("1", "王五", {"1": "李明"}), [ErrorCode.IDENTITY_CONFLICT]
        )

    def test_valid(self):
        self.assertEqual(validate_identity("1", "李明", {"1": "李明"}), [])
        self.assertEqual(validate_identity("1", None, {"1": "李明"}), [])


class TestDuplicate(unittest.TestCase):
    def test_duplicate_detected(self):
        self.assertEqual(
            check_duplicate_students(["1", "1", "2"]), [ErrorCode.IDENTITY_DUPLICATE]
        )

    def test_no_duplicate(self):
        self.assertEqual(check_duplicate_students(["1", "2"]), [])


if __name__ == "__main__":
    unittest.main()
