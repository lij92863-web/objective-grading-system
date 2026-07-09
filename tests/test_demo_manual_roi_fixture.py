import unittest

from app.recognition.manual_roi_schema import load_manual_roi_file, validate_manual_roi_file


class DemoManualROIFixtureTests(unittest.TestCase):
    def test_demo_roi_valid_and_complete(self):
        roi_file = load_manual_roi_file("tests/fixtures/recognition/single_image/demo_manual_roi.json")
        self.assertTrue(validate_manual_roi_file(roi_file)["valid"])
        self.assertGreaterEqual(len(roi_file.identity_rois), 1)
        self.assertGreaterEqual(len(roi_file.question_rois), 5)
        self.assertGreaterEqual(len(roi_file.blank_rois), 2)


if __name__ == "__main__":
    unittest.main()
