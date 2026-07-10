"""SRE1091 (part) — verify every required ErrorCode member exists.

Run: python -m unittest discover -s tests/student_recognition
"""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode

# Full expected enumeration, grouped by category (mirrors error_codes.py).
EXPECTED_CODES = [
    # Image
    "IMG_BLUR_TOO_HIGH",
    "IMG_TOO_DARK",
    "IMG_TOO_BRIGHT",
    "IMG_LOW_CONTRAST",
    "IMG_SHADOW_TOO_STRONG",
    "IMG_TOO_SMALL",
    "IMG_UNSUPPORTED_FORMAT",
    "IMG_UPLOAD_CORRUPTED",
    # Page
    "PAGE_NOT_FOUND",
    "PAGE_QUAD_INVALID",
    "PAGE_COVERAGE_TOO_SMALL",
    "PAGE_ASPECT_RATIO_INVALID",
    "PAGE_PERSPECTIVE_TOO_EXTREME",
    "PAGE_NORMALIZATION_FAILED",
    # Template
    "TEMPLATE_MISSING",
    "TEMPLATE_VERSION_MISSING",
    "TEMPLATE_VERSION_MISMATCH",
    "TEMPLATE_PAGE_MISSING",
    "TEMPLATE_ROI_OUT_OF_BOUNDS",
    "TEMPLATE_OPTION_CELL_MISSING",
    "TEMPLATE_IDENTITY_ROI_MISSING",
    "TEMPLATE_CALIBRATION_ANCHOR_INVALID",
    "TEMPLATE_COORDINATE_SYSTEM_INVALID",
    "TEMPLATE_ROI_INVALID",
    "TEMPLATE_DUPLICATE_QUESTION_NO",
    "TEMPLATE_INVALID_OPTION_LABEL",
    "TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS",
    "TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS",
    "TEMPLATE_QUESTION_BLOCK_EMPTY",
    "TEMPLATE_ROI_OVERLAP_WARNING",
    "TEMPLATE_DUPLICATE_PAGE_ID",
    "TEMPLATE_DUPLICATE_PAGE_NO",
    "TEMPLATE_VERSION_CONFLICT",
    "TEMPLATE_DRAFT_NOT_FINALIZED",
    "TEMPLATE_SCHEMA_INVALID",
    # Template (SRE945 v2 additions)
    "TEMPLATE_COORDINATE_SYSTEM_INVALID",
    "TEMPLATE_ROI_INVALID",
    "TEMPLATE_DUPLICATE_QUESTION_NO",
    "TEMPLATE_INVALID_OPTION_LABEL",
    "TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS",
    "TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS",
    "TEMPLATE_QUESTION_BLOCK_EMPTY",
    "TEMPLATE_ROI_OVERLAP_WARNING",
    "TEMPLATE_DUPLICATE_PAGE_ID",
    "TEMPLATE_DUPLICATE_PAGE_NO",
    "TEMPLATE_VERSION_CONFLICT",
    "TEMPLATE_DRAFT_NOT_FINALIZED",
    "TEMPLATE_SCHEMA_INVALID",
    # ROI
    "ROI_OUT_OF_BOUNDS",
    "ROI_EMPTY_CROP",
    "ROI_TOO_SMALL",
    "ROI_CROP_FAILED",
    # OMR
    "OMR_WEAK_MARK",
    "OMR_EMPTY_MARK",
    "OMR_MULTI_MARK_SINGLE_CHOICE",
    "OMR_AMBIGUOUS_MULTI_CHOICE",
    "OMR_BORDER_NOISE_HIGH",
    "OMR_ERASURE_DETECTED",
    "OMR_LOW_CONFIDENCE",
    "OMR_OPTION_CELL_MISSING",
    # Identity
    "IDENTITY_MISSING",
    "IDENTITY_LOW_CONFIDENCE",
    "IDENTITY_CONFLICT",
    "IDENTITY_DUPLICATE",
    "IDENTITY_ROSTER_NOT_FOUND",
    "IDENTITY_NAME_ONLY",
    "IDENTITY_STUDENT_ID_ONLY_UNMATCHED",
    # Draft / Review
    "DRAFT_HAS_BLOCKING_ERRORS",
    "DRAFT_HAS_UNRESOLVED_REVIEW",
    "REVIEW_ITEM_UNRESOLVED",
    "TEACHER_CONFIRMATION_REQUIRED",
    "TEACHER_OVERRIDE_REQUIRES_NOTE",
    # Bundle
    "BUNDLE_MISSING_PAGE",
    "BUNDLE_DUPLICATE_PAGE",
    "BUNDLE_IDENTITY_CONFLICT",
    "BUNDLE_TEMPLATE_VERSION_MISMATCH",
    "BUNDLE_PAGE_ORDER_UNKNOWN",
    # Grading Gate
    "GRADING_DRAFT_NOT_CONFIRMED",
    "GRADING_IDENTITY_NOT_CONFIRMED",
    "GRADING_BLOCKING_ERRORS_EXIST",
    "GRADING_UNRESOLVED_REVIEW_ITEMS",
    "GRADING_EXAM_HAS_DUPLICATE_STUDENT",
    "GRADING_EXAM_HAS_MISSING_STUDENTS",
    "GRADING_ANSWER_KEY_NOT_ACCEPTED",
    # Internal fallback
    "INTERNAL_UNKNOWN_ERROR",
]


class TestErrorCodesExist(unittest.TestCase):
    def test_all_expected_codes_present(self):
        existing = {member.name for member in ErrorCode}
        missing = [name for name in EXPECTED_CODES if name not in existing]
        self.assertEqual(missing, [], f"Missing ErrorCode members: {missing}")

    def test_values_are_stable_strings(self):
        for name in EXPECTED_CODES:
            member = ErrorCode[name]
            self.assertEqual(
                member.value,
                name,
                f"ErrorCode.{name} must have stable string value == name",
            )

    def test_no_unexpected_extra_codes(self):
        extra = {member.name for member in ErrorCode} - set(EXPECTED_CODES)
        self.assertEqual(extra, set(), f"Unexpected ErrorCode members: {extra}")

    def test_internal_unknown_error_is_fallback(self):
        self.assertEqual(ErrorCode.INTERNAL_UNKNOWN_ERROR.value, "INTERNAL_UNKNOWN_ERROR")


if __name__ == "__main__":
    unittest.main()
