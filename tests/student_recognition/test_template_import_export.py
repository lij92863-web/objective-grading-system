"""SRE945 §15.7 -- import / export roundtrip & schema rejection tests."""

import copy
import json
import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.template_profile import (
    TemplateProfile,
    export_template,
    import_template,
)
from app.student_recognition.template.template_validator import TemplateValidationError


def _valid_dict():
    return {
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
        "reference_canvas": {"width": 240, "height": 360, "source": "synthetic:synthetic-v1"},
        "pages": [
            {
                "template_page_id": "page_1",
                "page_no": 1,
                "anchors": [{"anchor_id": "choice_block_top_left", "x": 0.15, "y": 0.1333}],
                "identity": {
                    "combined_identity_roi": {"x": 0.0833, "y": 0.0333, "w": 0.8333, "h": 0.0667}
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
                        "blank_roi": {"dx": 0.0, "dy": 0.0, "w": 0.1833, "h": 0.03},
                    }
                ],
                "blank_rois": [],
            }
        ],
    }


class TestTemplateImportExport(unittest.TestCase):
    def test_template_export_import_roundtrip(self):
        profile = TemplateProfile.from_dict(_valid_dict())
        exported = profile.to_dict()
        reimported = TemplateProfile.from_dict(copy.deepcopy(exported))
        self.assertEqual(reimported.to_dict(), exported)

    def test_template_import_rejects_unknown_schema_without_adapter(self):
        bad = _valid_dict()
        bad["schema_version"] = "9.9"
        with self.assertRaises(TemplateValidationError) as ctx:
            TemplateProfile.from_dict(bad)
        self.assertEqual(
            ctx.exception.report.errors[0].code, ErrorCode.TEMPLATE_VERSION_MISMATCH
        )

    def test_template_import_preserves_coordinates(self):
        profile = TemplateProfile.from_dict(_valid_dict())
        exported = profile.to_dict()
        reimported = TemplateProfile.from_dict(exported)
        original_cells = profile.get_all_option_cells()
        restored_cells = reimported.get_all_option_cells()
        self.assertEqual(len(original_cells), len(restored_cells))
        for a, b in zip(original_cells, restored_cells):
            self.assertAlmostEqual(a.roi["x"], b.roi["x"], delta=1e-12)
            self.assertAlmostEqual(a.roi["y"], b.roi["y"], delta=1e-12)
            self.assertAlmostEqual(a.roi["w"], b.roi["w"], delta=1e-12)
            self.assertAlmostEqual(a.roi["h"], b.roi["h"], delta=1e-12)

    def test_template_canonical_export_is_byte_stable(self):
        first = export_template(TemplateProfile.from_dict(_valid_dict()))
        second = export_template(import_template(first))
        self.assertEqual(second, first)
        self.assertEqual(json.loads(first)["schema_version"], "2.0")

    def test_import_template_validates_before_returning_profile(self):
        bad = _valid_dict()
        bad["pages"][0]["identity"] = {}
        with self.assertRaises(TemplateValidationError) as ctx:
            import_template(bad)
        self.assertEqual(
            ctx.exception.report.errors[0].code,
            ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING,
        )

    def test_template_import_rejects_unknown_field(self):
        bad = _valid_dict()
        bad["unexpected"] = True
        with self.assertRaises(TemplateValidationError) as ctx:
            import_template(bad)
        self.assertEqual(
            ctx.exception.report.errors[0].code,
            ErrorCode.TEMPLATE_SCHEMA_INVALID,
        )
        self.assertEqual(ctx.exception.report.errors[0].path, "unexpected")


if __name__ == "__main__":
    unittest.main()
