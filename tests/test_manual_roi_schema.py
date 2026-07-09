import unittest
from copy import deepcopy
from pathlib import Path

from app.recognition.manual_roi_schema import ManualROIFile, load_manual_roi_file, validate_manual_roi_file


FIXTURE = "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class ManualROISchemaTests(unittest.TestCase):
    def roi_file(self):
        return load_manual_roi_file(FIXTURE)

    def test_valid_roi(self):
        self.assertTrue(validate_manual_roi_file(self.roi_file())["valid"])

    def test_missing_identity_fails(self):
        roi_file = self.roi_file()
        roi_file.identity_rois = []
        self.assertIn("MISSING_IDENTITY_ROI", validate_manual_roi_file(roi_file)["blockers"])

    def test_negative_x_fails(self):
        roi_file = self.roi_file()
        roi_file.question_rois[0].x = -1
        self.assertTrue(any(code.startswith("NEGATIVE_COORDINATE") for code in validate_manual_roi_file(roi_file)["blockers"]))

    def test_negative_y_fails(self):
        roi_file = self.roi_file()
        roi_file.question_rois[0].y = -1
        self.assertTrue(any(code.startswith("NEGATIVE_COORDINATE") for code in validate_manual_roi_file(roi_file)["blockers"]))

    def test_zero_width_fails(self):
        roi_file = self.roi_file()
        roi_file.question_rois[0].width = 0
        self.assertTrue(any(code.startswith("INVALID_ROI_SIZE") for code in validate_manual_roi_file(roi_file)["blockers"]))

    def test_zero_height_fails(self):
        roi_file = self.roi_file()
        roi_file.question_rois[0].height = 0
        self.assertTrue(any(code.startswith("INVALID_ROI_SIZE") for code in validate_manual_roi_file(roi_file)["blockers"]))

    def test_out_of_bounds_x_fails(self):
        roi_file = self.roi_file()
        roi_file.question_rois[0].x = 1199
        self.assertTrue(any(code.startswith("ROI_OUT_OF_BOUNDS") for code in validate_manual_roi_file(roi_file)["blockers"]))

    def test_out_of_bounds_y_fails(self):
        roi_file = self.roi_file()
        roi_file.question_rois[0].y = 1599
        self.assertTrue(any(code.startswith("ROI_OUT_OF_BOUNDS") for code in validate_manual_roi_file(roi_file)["blockers"]))

    def test_invalid_page_bounds_fails(self):
        roi_file = self.roi_file()
        roi_file.page_width = 0
        self.assertIn("INVALID_PAGE_BOUNDS", validate_manual_roi_file(roi_file)["blockers"])

    def test_missing_questions_fails(self):
        roi_file = self.roi_file()
        roi_file.question_rois = []
        roi_file.choice_cell_rois = []
        roi_file.blank_rois = []
        self.assertIn("MISSING_QUESTION_ROIS", validate_manual_roi_file(roi_file)["blockers"])

    def test_summary_counts(self):
        summary = validate_manual_roi_file(self.roi_file())["roi_summary"]
        self.assertGreaterEqual(summary["choice_cell_roi_count"], 10)

    def test_round_trip_dict(self):
        roi_file = self.roi_file()
        self.assertEqual(ManualROIFile.from_dict(roi_file.to_dict()).to_dict(), roi_file.to_dict())


if __name__ == "__main__":
    unittest.main()
