"""SRE945 -- TemplateValidator exhaustive rule coverage (§7 / §15 validator set)."""

import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_message import message_for
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template.template_validator import (
    TemplateValidator,
    ValidationReport,
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


def _report(d):
    return TemplateValidator().validate(TemplateProfile.from_dict(d))


def _codes(d):
    return {e.code for e in _report(d).errors}


class TestTemplateValidator(unittest.TestCase):
    def test_validator_accepts_well_formed(self):
        self.assertEqual(_report(_valid_dict()).status, "valid")

    def test_validator_rejects_bad_coordinate_system(self):
        d = _valid_dict()
        d["coordinate_system"]["type"] = "pixel"
        self.assertIn(ErrorCode.TEMPLATE_COORDINATE_SYSTEM_INVALID, _codes(d))

    def test_validator_rejects_missing_identity(self):
        d = _valid_dict()
        d["pages"][0]["identity"] = {}
        self.assertIn(ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING, _codes(d))

    def test_validator_rejects_duplicate_page_id(self):
        d = _valid_dict()
        page = dict(d["pages"][0])
        d["pages"].append(page)
        self.assertIn(ErrorCode.TEMPLATE_DUPLICATE_PAGE_ID, _codes(d))

    def test_validator_rejects_duplicate_page_no(self):
        d = _valid_dict()
        page = dict(d["pages"][0])
        page["template_page_id"] = "page_2"
        d["pages"].append(page)
        self.assertIn(ErrorCode.TEMPLATE_DUPLICATE_PAGE_NO, _codes(d))

    def test_validator_rejects_question_block_empty(self):
        d = _valid_dict()
        d["pages"][0]["question_blocks"] = []
        d["pages"][0]["blank_rois"] = []
        self.assertIn(ErrorCode.TEMPLATE_QUESTION_BLOCK_EMPTY, _codes(d))

    def test_validator_rejects_single_choice_missing_letters(self):
        d = _valid_dict()
        d["pages"][0]["question_blocks"][0]["options"] = ["A", "B", "C"]
        self.assertIn(ErrorCode.TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS, _codes(d))

    def test_validator_rejects_multi_choice_empty(self):
        d = _valid_dict()
        block = d["pages"][0]["question_blocks"][0]
        block["question_type"] = "multi_choice"
        block["options"] = []
        self.assertIn(ErrorCode.TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS, _codes(d))

    def test_validator_rejects_duplicate_question_no(self):
        d = _valid_dict()
        a = {
            "block_id": "a",
            "question_type": "single_choice",
            "question_range": [1, 5],
            "options": ["A", "B", "C", "D"],
            "anchor_id": "choice_block_top_left",
            "layout": {"row_gap": 0.05, "option_gap": 0.1, "cell_w": 0.1, "cell_h": 0.05, "columns": 1},
            "blank_roi": {"dx": 0.0, "dy": 0.0, "w": 0.1, "h": 0.02},
        }
        b = dict(a)
        b["block_id"] = "b"
        b["question_range"] = [4, 8]
        d["pages"][0]["question_blocks"] = [a, b]
        self.assertIn(ErrorCode.TEMPLATE_DUPLICATE_QUESTION_NO, _codes(d))

    def test_validator_rejects_out_of_bounds_option_cell(self):
        d = _valid_dict()
        # Huge option gap pushes later option cells past x=1.
        d["pages"][0]["question_blocks"][0]["layout"]["option_gap"] = 0.5
        self.assertIn(ErrorCode.TEMPLATE_ROI_OUT_OF_BOUNDS, _codes(d))

    def test_validator_emits_overlap_warning(self):
        d = _valid_dict()
        # Two fully-overlapping identity ROIs -> overlap warning.
        d["pages"][0]["identity"] = {
            "student_id_roi": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.1},
            "name_roi": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.1},
            "combined_identity_roi": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.1},
        }
        report = _report(d)
        warnings = {w.code for w in report.warnings}
        self.assertIn(ErrorCode.TEMPLATE_ROI_OVERLAP_WARNING, warnings)
        # Warnings must not block a valid template.
        self.assertEqual(report.status, "valid")

    def test_validator_report_message_from_catalog(self):
        d = _valid_dict()
        d["pages"][0]["identity"] = {}
        report = _report(d)
        self.assertTrue(report.errors)
        for err in report.errors:
            self.assertEqual(err.message, message_for(err.code))
            self.assertIsInstance(err.path, str)


if __name__ == "__main__":
    unittest.main()
