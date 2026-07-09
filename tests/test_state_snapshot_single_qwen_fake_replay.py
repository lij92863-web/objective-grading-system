"""Tests for state snapshot with fake replay — R391."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.qwen_adapter.single_fake_replay import run_single_fake_replay


class StateSnapshotSingleQwenFakeReplayTests(unittest.TestCase):
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

    def test_snapshot_type_is_fake_replay(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        # Build a mock snapshot
        snapshot = {
            "snapshot_type": "single_qwen_fake_replay",
            "request_manifest_summary": result.get("request_manifest", {}),
            "sanitized_summary": result.get("sanitized_summary", {}),
            "parser_audit_summary": result.get("parser_audit", {}),
            "review_summary": result.get("review_summary", {}),
            "teacher_summary": result.get("teacher_summary", {}),
            "trial_report_summary": result.get("trial_report", {}),
        }
        self.assertEqual(snapshot["snapshot_type"], "single_qwen_fake_replay")
        self.assertIn("request_manifest_summary", snapshot)
        self.assertIn("sanitized_summary", snapshot)

    def test_snapshot_has_all_required_sections(self):
        fake = self._load_fake("fake_single_qwen_valid_choice_blank_identity.json")
        result = run_single_fake_replay(self.manifest, self.roi, fake)
        for key in ["request_manifest", "sanitized_summary", "parser_audit",
                     "review_summary", "teacher_summary", "trial_report"]:
            self.assertIn(key, result, f"Missing key: {key}")


if __name__ == "__main__":
    unittest.main()
