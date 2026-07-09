"""SRE1091 (part) — verify the error policy flags match the constitution.

Run: python -m unittest discover -s tests/student_recognition
"""

import unittest

from app.student_recognition.errors.error_catalog import get_entry
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_policy import (
    can_teacher_override,
    is_blocking,
    requires_review,
)


class TestErrorPolicy(unittest.TestCase):
    def test_omr_multi_mark_single_choice_not_blocking_but_review(self):
        code = ErrorCode.OMR_MULTI_MARK_SINGLE_CHOICE
        self.assertFalse(is_blocking(code), "OMR multi-mark must NOT block")
        self.assertTrue(requires_review(code), "OMR multi-mark must require review")

    def test_identity_conflict_is_blocking(self):
        code = ErrorCode.IDENTITY_CONFLICT
        self.assertTrue(is_blocking(code), "Identity conflict must block")
        self.assertTrue(requires_review(code), "Identity conflict must require review")

    def test_grading_draft_not_confirmed_blocking_not_review(self):
        code = ErrorCode.GRADING_DRAFT_NOT_CONFIRMED
        self.assertTrue(is_blocking(code), "Unconfirmed draft must block grading")
        self.assertFalse(
            requires_review(code),
            "Gate rejection should not itself require a review item",
        )

    def test_unknown_code_maps_to_internal_and_is_blocking(self):
        # An unregistered code value must fail closed (blocking + review) and be
        # mapped to INTERNAL_UNKNOWN_ERROR. ErrorCode is str-based, so an arbitrary
        # non-member string exercises the exact fallback path used by the policy.
        unknown = "UNKNOWN_X"
        self.assertNotIn(unknown, {c.value for c in ErrorCode})

        entry = get_entry(unknown)
        self.assertEqual(entry.code, ErrorCode.INTERNAL_UNKNOWN_ERROR)
        self.assertTrue(entry.blocking)
        self.assertTrue(entry.requires_review)

        # The public policy helpers must also fail closed on the unknown value.
        self.assertTrue(is_blocking(unknown), "Unknown code must block (fail closed)")
        self.assertTrue(
            requires_review(unknown), "Unknown code must require review (fail closed)"
        )

    def test_teacher_override_flags_consistent(self):
        self.assertTrue(can_teacher_override(ErrorCode.IDENTITY_CONFLICT))
        self.assertFalse(can_teacher_override(ErrorCode.GRADING_DRAFT_NOT_CONFIRMED))


if __name__ == "__main__":
    unittest.main()
