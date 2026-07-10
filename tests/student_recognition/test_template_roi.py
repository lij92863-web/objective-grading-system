"""SRE945 §15.2 -- ROI validation tests (bounds / finite / positive)."""

import math
import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.coordinates import to_runtime_pixels
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


def _validate(d):
    return TemplateValidator().validate(TemplateProfile.from_dict(d, _validate=False))


class TestTemplateRoi(unittest.TestCase):
    def test_template_rejects_roi_out_of_bounds(self):
        d = _valid_dict()
        d["pages"][0]["identity"]["combined_identity_roi"] = {
            "x": 0.5,
            "y": 0.5,
            "w": 0.8,
            "h": 0.8,
        }
        report = _validate(d)
        codes = {e.code for e in report.errors}
        self.assertIn(ErrorCode.TEMPLATE_ROI_OUT_OF_BOUNDS, codes)

    def test_template_rejects_negative_roi_width(self):
        d = _valid_dict()
        d["pages"][0]["identity"]["combined_identity_roi"] = {
            "x": 0.1,
            "y": 0.1,
            "w": -0.1,
            "h": 0.1,
        }
        report = _validate(d)
        self.assertIn(ErrorCode.TEMPLATE_ROI_INVALID, {e.code for e in report.errors})

    def test_template_rejects_negative_roi_height(self):
        d = _valid_dict()
        d["pages"][0]["identity"]["combined_identity_roi"] = {
            "x": 0.1,
            "y": 0.1,
            "w": 0.1,
            "h": -0.1,
        }
        report = _validate(d)
        self.assertIn(ErrorCode.TEMPLATE_ROI_INVALID, {e.code for e in report.errors})

    def test_template_rejects_zero_size_roi(self):
        d = _valid_dict()
        d["pages"][0]["identity"]["combined_identity_roi"] = {
            "x": 0.1,
            "y": 0.1,
            "w": 0.0,
            "h": 0.1,
        }
        report = _validate(d)
        self.assertIn(ErrorCode.TEMPLATE_ROI_INVALID, {e.code for e in report.errors})

    def test_template_rejects_nan_roi(self):
        d = _valid_dict()
        roi = {"x": 0.1, "y": 0.1, "w": 0.1, "h": float("nan")}
        d["pages"][0]["identity"]["combined_identity_roi"] = roi
        report = _validate(d)
        self.assertIn(ErrorCode.TEMPLATE_ROI_INVALID, {e.code for e in report.errors})

    def test_template_rejects_null_roi(self):
        d = _valid_dict()
        roi = {"x": 0.1, "y": 0.1, "w": None, "h": 0.1}
        d["pages"][0]["identity"]["combined_identity_roi"] = roi
        report = _validate(d)
        self.assertIn(ErrorCode.TEMPLATE_ROI_INVALID, {e.code for e in report.errors})

    def test_coordinates_to_runtime_pixels_maps_norm_by_size(self):
        norm = {"x": 0.5, "y": 0.25, "w": 0.5, "h": 0.5}
        px = to_runtime_pixels(norm, 240, 360)
        self.assertEqual(px, {"x": 120, "y": 90, "w": 120, "h": 180})

    def test_coordinates_to_runtime_pixels_boundaries(self):
        # Edge values must not overflow the runtime canvas.
        norm = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
        px = to_runtime_pixels(norm, 100, 200)
        self.assertEqual(px, {"x": 0, "y": 0, "w": 100, "h": 200})

    def test_coordinates_rejects_non_finite(self):
        with self.assertRaises(ValueError):
            to_runtime_pixels({"x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1}, 0, 100)


if __name__ == "__main__":
    unittest.main()
