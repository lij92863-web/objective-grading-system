"""SRE945 §15.1 -- TemplateProfile v2 schema tests.

Every assertion checks a specific constitutional ``ErrorCode`` (constitution B6),
not a free-form string.
"""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template import (
    Anchor,
    BlankROI,
    BubbleGrid,
    CoordinateSystem,
    IdentityRegion,
    QuestionBlock,
    ROIBox,
    ReferenceCanvas,
    TemplatePage,
)
from app.student_recognition.template.template_validator import (
    TemplateValidationError,
)


def _valid_dict(**overrides):
    base = {
        "schema_version": "2.0",
        "template_id": "objective_sheet_v1",
        "template_name": "测试模板",
        "template_version": 1,
        "coordinate_system": {
            "type": "normalized",
            "origin": "top_left",
            "unit": "ratio",
            "x_range": [0.0, 1.0],
            "y_range": [0.0, 1.0],
        },
        "reference_canvas": {
            "width": 240,
            "height": 360,
            "source": "synthetic:synthetic-v1",
        },
        "pages": [
            {
                "template_page_id": "page_1",
                "page_no": 1,
                "anchors": [
                    {"anchor_id": "choice_block_top_left", "x": 0.15, "y": 0.1333}
                ],
                "identity": {
                    "combined_identity_roi": {
                        "x": 0.0833,
                        "y": 0.0333,
                        "w": 0.8333,
                        "h": 0.0667,
                    }
                },
                "question_blocks": [
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
                        "blank_roi": {
                            "dx": 0.0,
                            "dy": 0.0,
                            "w": 0.1833,
                            "h": 0.03,
                        },
                    }
                ],
                "blank_rois": [],
            }
        ],
    }
    base.update(overrides)
    return base


def _first_code(exc):
    return exc.report.errors[0].code


class TestTemplateProfileSchema(unittest.TestCase):
    def test_template_profile_requires_schema_version(self):
        data = _valid_dict()
        del data["schema_version"]
        with self.assertRaises(TemplateValidationError) as ctx:
            TemplateProfile.from_dict(data)
        self.assertEqual(_first_code(ctx.exception), ErrorCode.TEMPLATE_VERSION_MISSING)

    def test_template_profile_requires_template_id(self):
        data = _valid_dict()
        del data["template_id"]
        with self.assertRaises(TemplateValidationError) as ctx:
            TemplateProfile.from_dict(data)
        self.assertEqual(_first_code(ctx.exception), ErrorCode.TEMPLATE_MISSING)

    def test_template_profile_requires_template_version(self):
        data = _valid_dict()
        del data["template_version"]
        with self.assertRaises(TemplateValidationError) as ctx:
            TemplateProfile.from_dict(data)
        self.assertEqual(_first_code(ctx.exception), ErrorCode.TEMPLATE_VERSION_MISSING)

    def test_template_profile_rejects_missing_page(self):
        data = _valid_dict(pages=[])
        with self.assertRaises(TemplateValidationError) as ctx:
            TemplateProfile.from_dict(data)
        self.assertEqual(_first_code(ctx.exception), ErrorCode.TEMPLATE_PAGE_MISSING)

    def test_template_profile_rejects_invalid_coordinate_system(self):
        data = _valid_dict()
        data["coordinate_system"] = {
            "type": "pixel",
            "origin": "top_left",
            "unit": "px",
        }
        with self.assertRaises(TemplateValidationError) as ctx:
            TemplateProfile.from_dict(data)
        self.assertEqual(
            _first_code(ctx.exception), ErrorCode.TEMPLATE_COORDINATE_SYSTEM_INVALID
        )

    def test_template_profile_auto_adapts_v1_synthetic(self):
        # A legacy synthetic v1 dict (schema_version == 1) must be promoted
        # automatically to v2 without raising.
        from app.student_recognition.synthetic.template_profile import (
            build_default_template,
        )

        v1_dict = build_default_template().to_dict()
        self.assertEqual(v1_dict["schema_version"], 1)
        profile = TemplateProfile.from_dict(v1_dict)
        self.assertEqual(profile.schema_version, "2.0")
        self.assertEqual(profile.template_id, "synthetic-v1")

    def test_explicit_schema_value_objects_serialize(self):
        roi = ROIBox(0.1, 0.2, 0.3, 0.4)
        grid = BubbleGrid(0.05, 0.06, 0.02, 0.01)
        block = QuestionBlock("b1", "single_choice", [1, 2], ["A", "B", "C", "D"], "a1", grid)
        page = TemplatePage(
            "page_1",
            1,
            anchors=[Anchor("a1", 0.1, 0.2)],
            identity=IdentityRegion(combined_identity_roi=roi),
            question_blocks=[block],
            blank_rois=[BlankROI(3, roi)],
        )
        self.assertEqual(CoordinateSystem().to_dict()["type"], "normalized")
        self.assertEqual(ReferenceCanvas(240, 360, "synthetic:test").to_dict()["width"], 240)
        self.assertEqual(page.to_dict()["identity"]["combined_identity_roi"], roi.to_dict())


if __name__ == "__main__":
    unittest.main()
