"""SRE945 §15.4 -- identity ROI tests."""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template.template_validator import TemplateValidator


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
    base.update(overrides)
    return base


def _codes(d):
    report = TemplateValidator().validate(TemplateProfile.from_dict(d))
    return {e.code for e in report.errors}


class TestTemplateIdentity(unittest.TestCase):
    def test_template_requires_identity_roi(self):
        d = _valid_dict()
        d["pages"][0]["identity"] = {}
        self.assertIn(ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING, _codes(d))

    def test_template_accepts_combined_identity_roi(self):
        d = _valid_dict()
        combined = {"x": 0.08, "y": 0.03, "w": 0.83, "h": 0.07}
        d["pages"][0]["identity"] = {"combined_identity_roi": combined}
        profile = TemplateProfile.from_dict(d)
        got = profile.get_identity_roi()
        self.assertEqual(got["x"], combined["x"])
        self.assertEqual(got["w"], combined["w"])

    def test_template_rejects_identity_roi_out_of_bounds(self):
        d = _valid_dict()
        d["pages"][0]["identity"] = {
            "combined_identity_roi": {"x": 0.5, "y": 0.5, "w": 0.8, "h": 0.8}
        }
        self.assertIn(ErrorCode.TEMPLATE_ROI_OUT_OF_BOUNDS, _codes(d))

    def test_template_identity_prefers_combined_over_split(self):
        d = _valid_dict()
        d["pages"][0]["identity"] = {
            "student_id_roi": {"x": 0.0, "y": 0.0, "w": 0.4, "h": 0.05},
            "name_roi": {"x": 0.5, "y": 0.0, "w": 0.4, "h": 0.05},
            "combined_identity_roi": {"x": 0.0, "y": 0.0, "w": 0.9, "h": 0.05},
        }
        profile = TemplateProfile.from_dict(d)
        self.assertEqual(profile.get_identity_roi()["w"], 0.9)

    def test_template_identity_union_when_no_combined(self):
        d = _valid_dict()
        d["pages"][0]["identity"] = {
            "student_id_roi": {"x": 0.0, "y": 0.0, "w": 0.4, "h": 0.05},
            "name_roi": {"x": 0.5, "y": 0.0, "w": 0.4, "h": 0.05},
        }
        profile = TemplateProfile.from_dict(d)
        roi = profile.get_identity_roi()
        # Union spans from x=0.0 to x=0.9 with full height.
        self.assertAlmostEqual(roi["x"], 0.0)
        self.assertAlmostEqual(roi["w"], 0.9)


if __name__ == "__main__":
    unittest.main()
