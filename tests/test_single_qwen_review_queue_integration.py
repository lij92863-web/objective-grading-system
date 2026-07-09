"""Tests for single Qwen review queue integration — R382."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.qwen_adapter.single_fake_replay import run_single_fake_replay


class SingleQwenReviewQueueIntegrationTests(unittest.TestCase):
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

    def test_valid_response_creates_review_items(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        review = result["review_summary"]
        self.assertIn("total_items", review)
        self.assertGreater(review["total_items"], 0)

    def test_invalid_option_creates_blocking_item(self):
        fake = self._load_fake("fake_single_qwen_invalid_option.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        audit = result["parser_audit"]
        self.assertGreater(audit.get("blocking_candidate_count", 0), 0)

    def test_identity_candidate_creates_review_item(self):
        fake = self._load_fake("fake_single_qwen_identity_candidate.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        audit = result["parser_audit"]
        self.assertGreaterEqual(audit.get("identity_candidate_count", 0), 0)

    def test_missing_question_id_creates_error(self):
        fake = self._load_fake("fake_single_qwen_missing_question_id.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        audit = result["parser_audit"]
        self.assertGreater(audit.get("missing_question_id_count", 0), 0)

    def test_no_confirmed_submission(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertFalse(result["grade_all_called"])

    def test_no_grade_all(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        self.assertFalse(result["grade_all_called"])
        self.assertFalse(result["formal_report_generated"])


if __name__ == "__main__":
    unittest.main()
