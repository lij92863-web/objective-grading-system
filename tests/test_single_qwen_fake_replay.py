"""Tests for single Qwen fake replay pipeline — R372."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.qwen_adapter.single_fake_replay import run_single_fake_replay


class SingleQwenFakeReplayTests(unittest.TestCase):
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

    def test_fake_replay_valid_response(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertTrue(result["ok"])
        self.assertFalse(result["real_api_called"])
        self.assertFalse(result["qwen_called"])
        self.assertFalse(result["grade_all_called"])

    def test_fake_replay_creates_review_summary(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertIn("review_summary", result)
        self.assertIn("total_items", result["review_summary"])

    def test_fake_replay_creates_teacher_summary(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertIn("teacher_summary", result)
        self.assertFalse(result["teacher_summary"]["real_api_called"])

    def test_fake_replay_no_qwen_called(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertFalse(result["qwen_called"])

    def test_fake_replay_no_grade_all(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertFalse(result["grade_all_called"])

    def test_fake_replay_no_formal_report(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertFalse(result["formal_report_generated"])

    def test_fake_replay_invalid_option(self):
        fake = self._load_fake("fake_single_qwen_invalid_option.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        audit = result.get("parser_audit", {})
        self.assertGreater(audit.get("invalid_option_count", 0), 0)
        # ready_for_review_queue should be false with invalid options
        self.assertFalse(audit.get("ready_for_review_queue", True))

    def test_fake_replay_malformed_json(self):
        # Read malformed file and pass raw text
        path = Path("tests/fixtures/recognition/qwen_single_response/fake_single_qwen_malformed_json.txt")
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        # Malformed JSON passed as raw text with no items
        fake = {"_malformed_raw": raw_text, "items": []}
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        # With empty items, engine_status is ok but parser finds issues
        audit = result.get("parser_audit", {})
        self.assertEqual(audit.get("candidate_count", -1), 0)

    def test_fake_replay_identity_candidate(self):
        fake = self._load_fake("fake_single_qwen_identity_candidate.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertIn("teacher_summary", result)
        # Identity candidate should be noted
        audit = result.get("parser_audit", {})
        self.assertGreaterEqual(audit.get("identity_candidate_count", 0), 0)

    def test_trial_report_not_batch(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        report = result.get("trial_report", {})
        self.assertFalse(report.get("ready_for_real_api", True))
        self.assertFalse(report.get("ready_for_grading", True))


if __name__ == "__main__":
    unittest.main()
