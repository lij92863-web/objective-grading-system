"""SRE945 §15.3 -- question / option expansion & validation tests."""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template.template_validator import (
    TemplateValidationError,
    TemplateValidator,
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
                        "question_range": [1, 10],
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
    report = TemplateValidator().validate(TemplateProfile.from_dict(d, _validate=False))
    return {e.code for e in report.errors}


class TestTemplateQuestionsOptions(unittest.TestCase):
    def test_template_rejects_duplicate_question_no(self):
        d = _valid_dict()
        # Two blocks whose ranges overlap on questions 5..10.
        block_a = dict(d["pages"][0]["question_blocks"][0])
        block_a = {
            "block_id": "a",
            "question_type": "single_choice",
            "question_range": [1, 6],
            "options": ["A", "B", "C", "D"],
            "anchor_id": "choice_block_top_left",
            "layout": {"row_gap": 0.05, "option_gap": 0.1, "cell_w": 0.1, "cell_h": 0.05, "columns": 1},
            "blank_roi": {"dx": 0.0, "dy": 0.0, "w": 0.1, "h": 0.02},
        }
        block_b = dict(block_a)
        block_b["block_id"] = "b"
        block_b["question_range"] = [5, 10]
        d["pages"][0]["question_blocks"] = [block_a, block_b]
        self.assertIn(ErrorCode.TEMPLATE_DUPLICATE_QUESTION_NO, _codes(d))

    def test_template_rejects_missing_option_cell(self):
        d = _valid_dict()
        d["pages"][0]["question_blocks"][0]["options"] = []
        self.assertIn(ErrorCode.TEMPLATE_OPTION_CELL_MISSING, _codes(d))

    def test_template_rejects_invalid_option_label(self):
        d = _valid_dict()
        d["pages"][0]["question_blocks"][0]["options"] = [1, 2, 3]
        self.assertIn(ErrorCode.TEMPLATE_INVALID_OPTION_LABEL, _codes(d))

    def test_template_expands_choice_grid(self):
        d = _valid_dict()
        d["pages"][0]["question_blocks"][0]["question_range"] = [1, 10]
        profile = TemplateProfile.from_dict(d)
        cells = profile.get_all_option_cells()
        self.assertEqual(len(cells), 40)  # 10 questions * 4 options
        q1 = profile.get_option_cells(1)
        self.assertEqual(len(q1), 4)
        self.assertEqual({c.option_label for c in q1}, {"A", "B", "C", "D"})

    def test_template_expanded_grid_rois_are_in_bounds(self):
        d = _valid_dict()
        d["pages"][0]["question_blocks"][0]["question_range"] = [1, 10]
        profile = TemplateProfile.from_dict(d)
        for cell in profile.get_all_option_cells():
            roi = cell.roi
            self.assertGreaterEqual(roi["x"], 0.0)
            self.assertGreaterEqual(roi["y"], 0.0)
            self.assertLessEqual(roi["x"] + roi["w"], 1.0 + 1e-9)
            self.assertLessEqual(roi["y"] + roi["h"], 1.0 + 1e-9)

    def test_template_single_choice_requires_abcd(self):
        d = _valid_dict()
        d["pages"][0]["question_blocks"][0]["options"] = ["A", "B", "C"]
        self.assertIn(ErrorCode.TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS, _codes(d))

    def test_template_multi_choice_requires_options(self):
        d = _valid_dict()
        block = d["pages"][0]["question_blocks"][0]
        block["question_type"] = "multi_choice"
        block["options"] = []
        self.assertIn(ErrorCode.TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS, _codes(d))


if __name__ == "__main__":
    unittest.main()
