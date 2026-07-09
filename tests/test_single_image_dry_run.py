import unittest

from app.recognition.single_image_dry_run import run_single_image_dry_run


MANIFEST = "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"
ROI = "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class SingleImageDryRunTests(unittest.TestCase):
    def test_demo_success(self):
        result = run_single_image_dry_run(MANIFEST, ROI)
        self.assertTrue(result["valid"])
        self.assertIn("review_summary", result)
        self.assertIn("teacher_summary", result)
        self.assertFalse(result["qwen_called"])
        self.assertFalse(result["grade_all_called"])
        self.assertFalse(result["formal_report_generated"])

    def test_missing_manifest_fails(self):
        self.assertFalse(run_single_image_dry_run("missing.json", ROI)["valid"])

    def test_missing_roi_fails(self):
        self.assertFalse(run_single_image_dry_run(MANIFEST, "missing.json")["valid"])


if __name__ == "__main__":
    unittest.main()
