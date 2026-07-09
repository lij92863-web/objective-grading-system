import unittest

from app.recognition.single_image_dry_run import run_single_image_dry_run
from app.recognition.single_image_trial_report import build_single_image_trial_report


class SingleImageTrialReportTests(unittest.TestCase):
    def test_report_safety_defaults(self):
        report = build_single_image_trial_report(run_single_image_dry_run(
            "tests/fixtures/recognition/single_image/demo_single_image_manifest.json",
            "tests/fixtures/recognition/single_image/demo_manual_roi.json",
        ), "demo")
        data = report.to_safe_dict()
        self.assertFalse(data["real_api_called"])
        self.assertFalse(data["raw_response_saved"])
        self.assertFalse(data["base64_emitted"])
        self.assertFalse(data["ready_for_real_api"])
        self.assertIn("do not start batch", data["next_step"])


if __name__ == "__main__":
    unittest.main()
