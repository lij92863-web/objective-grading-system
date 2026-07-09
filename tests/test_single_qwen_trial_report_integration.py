"""Tests for trial report integration — R383."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.qwen_adapter.single_fake_replay import run_single_fake_replay


class SingleQwenTrialReportIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_single_image_manifest(
            "tests/fixtures/recognition/single_image/demo_single_image_manifest.json")
        cls.roi = load_manual_roi_file(
            "tests/fixtures/recognition/single_image/demo_manual_roi.json")

    def _load_fake(self, name):
        path = Path("tests/fixtures/recognition/qwen_single_response") / name
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_real_api_called_false(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        report = result["trial_report"]
        self.assertFalse(report["real_api_called"])

    def test_raw_response_saved_false(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        report = result["trial_report"]
        self.assertFalse(report["raw_response_saved"])

    def test_base64_emitted_false(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        report = result["trial_report"]
        self.assertFalse(report["base64_emitted"])

    def test_ready_for_real_api_false(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        report = result["trial_report"]
        self.assertFalse(report["ready_for_real_api"])

    def test_ready_for_grading_false(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        report = result["trial_report"]
        self.assertFalse(report["ready_for_grading"])

    def test_next_step_not_recommend_batch(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        report = result["trial_report"]
        self.assertIn("do not start batch", report.get("next_step", "").lower() or
                       "not" in report.get("next_step", "").lower())


if __name__ == "__main__":
    unittest.main()
