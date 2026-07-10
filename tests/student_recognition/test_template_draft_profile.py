"""SRE945 §15.5 -- TemplateDraft vs TemplateProfile (the validation boundary)."""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.template_draft import TemplateDraft
from app.student_recognition.template.template_profile import (
    SCHEMA_VERSION,
    TemplateProfile,
)
from app.student_recognition.template.template_validator import (
    TemplateValidationError,
    TemplateValidator,
)


def _build_valid_draft(template_id="objective_sheet_v1"):
    draft = TemplateDraft(
        template_id=template_id,
        template_name="测试模板",
        template_version=1,
        reference_canvas={"width": 240, "height": 360, "source": "synthetic:synthetic-v1"},
    )
    draft.add_page(
        template_page_id="page_1",
        page_no=1,
        anchors=[{"anchor_id": "choice_block_top_left", "x": 0.15, "y": 0.1333}],
        identity={
            "combined_identity_roi": {"x": 0.0833, "y": 0.0333, "w": 0.8333, "h": 0.0667}
        },
        question_blocks=[
            {
                "block_id": "choice_block_1",
                "question_type": "single_choice",
                "question_range": [1, 12],
                "options": ["A", "B", "C", "D"],
                "anchor_id": "choice_block_top_left",
                "layout": {
                    "row_gap": 0.0722,
                    "option_gap": 0.1833,
                    "cell_w": 0.1833,
                    "cell_h": 0.0722,
                    "columns": 1,
                },
                "blank_roi": {"dx": 0.0, "dy": 0.0, "w": 0.1833, "h": 0.03},
            }
        ],
    )
    return draft


class TestTemplateDraftProfile(unittest.TestCase):
    def test_template_draft_cannot_be_used_for_recognition(self):
        draft = _build_valid_draft()
        with self.assertRaises(TemplateValidationError) as ctx:
            draft.get_option_cells(1)
        self.assertEqual(
            ctx.exception.report.errors[0].code, ErrorCode.TEMPLATE_DRAFT_NOT_FINALIZED
        )

    def test_valid_draft_can_be_finalized_to_profile(self):
        draft = _build_valid_draft()
        profile = draft.finalize()
        self.assertIsInstance(profile, TemplateProfile)
        self.assertEqual(profile.schema_version, SCHEMA_VERSION)
        # The finalized product exposes the frozen consumer interface.
        self.assertTrue(hasattr(profile, "get_option_cells"))
        report = TemplateValidator().validate(profile)
        self.assertEqual(report.status, "valid")
        self.assertEqual(len(profile.get_option_cells(1)), 4)

    def test_invalid_draft_cannot_finalize(self):
        draft = _build_valid_draft()
        # Remove the identity ROI so the draft is invalid.
        draft.pages[0]["identity"] = {}
        with self.assertRaises(TemplateValidationError) as ctx:
            draft.finalize()
        self.assertEqual(ctx.exception.report.status, "invalid")
        codes = {e.code for e in ctx.exception.report.errors}
        self.assertIn(ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING, codes)


if __name__ == "__main__":
    unittest.main()
