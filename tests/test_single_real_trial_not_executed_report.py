"""Tests for not-executed report — R375."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_real_trial_not_executed_report import (
    SingleRealTrialNotExecutedReport,
    build_not_executed_report,
)


class SingleRealTrialNotExecutedReportTests(unittest.TestCase):
    def test_real_api_called_always_false(self):
        report = build_not_executed_report()
        self.assertFalse(report.real_api_called)

    def test_api_key_present_boolean_only(self):
        report = build_not_executed_report(api_key_present=True)
        self.assertTrue(report.api_key_present)
        self.assertTrue(isinstance(report.api_key_present, bool))

    def test_no_api_key_value_in_output(self):
        report = build_not_executed_report(api_key_present=True)
        d = report.to_dict()
        raw = json.dumps(d)
        self.assertNotIn("sk-", raw)

    def test_no_image_base64_in_output(self):
        report = build_not_executed_report()
        d = report.to_dict()
        raw = json.dumps(d)
        self.assertNotIn("data:image", raw)

    def test_does_not_recommend_batch(self):
        report = build_not_executed_report()
        for step in report.next_required_steps:
            step_lower = step.lower()
            # "do not start batch" is OK — it's prohibiting batch
            if "batch" in step_lower and "do not" not in step_lower and "don't" not in step_lower:
                self.fail(f"Step recommends batch: {step}")

    def test_has_next_steps(self):
        report = build_not_executed_report()
        self.assertGreater(len(report.next_required_steps), 0)

    def test_json_round_trip(self):
        report = build_not_executed_report()
        d = report.to_dict()
        raw = json.dumps(d)
        parsed = json.loads(raw)
        self.assertEqual(parsed["real_api_called"], False)

    def test_custom_prerequisites(self):
        report = build_not_executed_report(
            missing_prerequisites=["no image", "no key"])
        self.assertIn("no image", report.missing_prerequisites)
        self.assertIn("no key", report.missing_prerequisites)


if __name__ == "__main__":
    unittest.main()
