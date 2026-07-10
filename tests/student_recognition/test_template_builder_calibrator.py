"""SRE945-F -- Calibrator (Level 1) + Level 0 JSON + Level 2 interface tests."""

import json
import tempfile
import unittest
from pathlib import Path

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.synthetic.template_profile import build_default_template
from app.student_recognition.template_builder.calibrator import Calibrator
from app.student_recognition.template_builder.level0_json import (
    read_validated_template,
    validate_template_dict,
)
from app.student_recognition.template_builder.level2_interface import VisualCalibrator
from app.student_recognition.template.template_validator import TemplateValidationError


def _valid_grid_anchors():
    return [{"anchor_id": "a1", "x": 0.1, "y": 0.1, "description": "top-left"}]


def _valid_block(anchor_id="a1", question_range=(1, 5), qtype="single_choice", options=None):
    return {
        "block_id": "b1",
        "question_type": qtype,
        "question_range": list(question_range),
        "options": options if options is not None else ["A", "B", "C", "D"],
        "anchor_id": anchor_id,
        "layout": {
            "row_gap": 0.05,
            "option_gap": 0.1,
            "cell_w": 0.08,
            "cell_h": 0.03,
            "columns": 1,
        },
        "blank_roi": {"dx": 0.0, "dy": 0.04, "w": 0.08, "h": 0.02},
    }


def _valid_identity():
    return {"combined_identity_roi": {"x": 0.1, "y": 0.02, "w": 0.8, "h": 0.05}}


def _four_corners():
    return [
        {"anchor_id": "top_left", "x": 0.1, "y": 0.1},
        {"anchor_id": "top_right", "x": 0.9, "y": 0.1},
        {"anchor_id": "bottom_right", "x": 0.9, "y": 0.9},
        {"anchor_id": "bottom_left", "x": 0.1, "y": 0.9},
    ]


class TestCalibrator(unittest.TestCase):
    def test_calibrate_from_synthetic_is_valid(self):
        cal = Calibrator()
        profile = cal.calibrate_from_synthetic(
            build_default_template(), template_id="objective_sheet_v1"
        )
        self.assertEqual(profile.template_id, "objective_sheet_v1")
        self.assertEqual(len(profile.get_option_cells(1)), 4)

    def test_calibrate_from_anchors_grid_origin(self):
        cal = Calibrator()
        profile = cal.calibrate_from_anchors(
            reference_canvas={"width": 240, "height": 360, "source": "manual"},
            anchors=_valid_grid_anchors(),
            blocks=[_valid_block()],
            identity=_valid_identity(),
            question_range=[1, 5],
        )
        self.assertEqual(profile.question_count(), 5)
        self.assertEqual(len(profile.get_option_cells(3)), 4)

    def test_calibrate_from_anchors_four_corner(self):
        cal = Calibrator()
        profile = cal.calibrate_from_anchors(
            reference_canvas={"width": 240, "height": 360, "source": "manual"},
            anchors=_four_corners(),
            blocks=[_valid_block(anchor_id="top_left")],
            identity=_valid_identity(),
            question_range=[1, 5],
            anchor_mode="four_corner",
        )
        cells = profile.get_option_cells(1)
        self.assertEqual(len(cells), 4)
        for cell in profile.get_all_option_cells():
            for v in (cell.roi["x"], cell.roi["y"], cell.roi["w"], cell.roi["h"]):
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_calibrate_from_anchors_four_corner_rejects_missing_corner(self):
        cal = Calibrator()
        # Only 3 of the 4 required corners -> invalid anchor config.
        bad = _four_corners()[:-1]
        with self.assertRaises(TemplateValidationError) as ctx:
            cal.calibrate_from_anchors(
                reference_canvas={"width": 240, "height": 360, "source": "manual"},
                anchors=bad,
                blocks=[_valid_block(anchor_id="top_left")],
                identity=_valid_identity(),
                question_range=[1, 5],
                anchor_mode="four_corner",
            )
        self.assertEqual(
            ctx.exception.report.errors[0].code,
            ErrorCode.TEMPLATE_CALIBRATION_ANCHOR_INVALID,
        )

    def test_level0_json_reads_validated_template(self):
        data = {
            "schema_version": "2.0",
            "template_id": "lvl0",
            "template_version": 1,
            "coordinate_system": {
                "type": "normalized",
                "origin": "top_left",
                "unit": "ratio",
                "x_range": [0.0, 1.0],
                "y_range": [0.0, 1.0],
            },
            "reference_canvas": {"width": 240, "height": 360, "source": "manual"},
            "pages": [
                {
                    "template_page_id": "page_1",
                    "page_no": 1,
                    "anchors": _valid_grid_anchors(),
                    "identity": _valid_identity(),
                    "question_blocks": [_valid_block()],
                    "blank_rois": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lvl0.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            profile = read_validated_template(path)
            self.assertEqual(profile.template_id, "lvl0")

    def test_level0_json_rejects_invalid(self):
        data = {
            "schema_version": "2.0",
            "template_id": "lvl0",
            "template_version": 1,
            "coordinate_system": {
                "type": "normalized",
                "origin": "top_left",
                "unit": "ratio",
                "x_range": [0.0, 1.0],
                "y_range": [0.0, 1.0],
            },
            "reference_canvas": {"width": 240, "height": 360, "source": "manual"},
            "pages": [
                {
                    "template_page_id": "page_1",
                    "page_no": 1,
                    "anchors": _valid_grid_anchors(),
                    "identity": {},  # missing identity -> invalid
                    "question_blocks": [_valid_block()],
                    "blank_rois": [],
                }
            ],
        }
        with self.assertRaises(TemplateValidationError):
            validate_template_dict(data)

    def test_level2_visual_calibrator_is_abstract(self):
        with self.assertRaises(TypeError):
            VisualCalibrator()  # must not be instantiable without implementation


if __name__ == "__main__":
    unittest.main()
