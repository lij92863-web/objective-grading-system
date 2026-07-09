"""Tests for SingleQwenRequestManifest — R365."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.single_request_manifest import (
    SingleQwenRequestManifest,
    build_request_manifest,
    validate_request_manifest,
    safe_request_manifest_summary,
)
from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file


class SingleQwenRequestManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_single_image_manifest(
            "tests/fixtures/recognition/single_image/demo_single_image_manifest.json")
        cls.roi = load_manual_roi_file(
            "tests/fixtures/recognition/single_image/demo_manual_roi.json")

    def test_real_api_allowed_false_by_default(self):
        m = SingleQwenRequestManifest()
        self.assertFalse(m.real_api_allowed)

    def test_check_only_true_by_default(self):
        m = SingleQwenRequestManifest()
        self.assertTrue(m.check_only)

    def test_raw_response_saved_false(self):
        m = SingleQwenRequestManifest()
        self.assertFalse(m.raw_response_saved)

    def test_base64_emitted_false(self):
        m = SingleQwenRequestManifest()
        self.assertFalse(m.base64_emitted)

    def test_api_key_present_boolean_only(self):
        m = SingleQwenRequestManifest(api_key_present=True)
        self.assertTrue(isinstance(m.api_key_present, bool))

    def test_no_api_key_in_output(self):
        m = SingleQwenRequestManifest(api_key_present=True)
        d = m.to_dict()
        raw = json.dumps(d)
        self.assertNotIn("sk-", raw)

    def test_no_base64_in_output(self):
        m = SingleQwenRequestManifest()
        d = m.to_dict()
        raw = json.dumps(d)
        self.assertNotIn("data:image", raw)

    def test_no_full_image_path_in_summary(self):
        m = build_request_manifest(self.manifest, self.roi)
        summary = safe_request_manifest_summary(m)
        raw = json.dumps(summary)
        self.assertNotIn("C:\\", raw)
        self.assertNotIn("Administrator", raw)

    def test_json_serializable(self):
        m = build_request_manifest(self.manifest, self.roi)
        d = m.to_dict()
        json_str = json.dumps(d)
        self.assertTrue(len(json_str) > 0)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["check_only"], True)
        self.assertEqual(parsed["real_api_allowed"], False)

    def test_validate_blocks_raw_response_saved(self):
        m = SingleQwenRequestManifest(raw_response_saved=True)
        result = validate_request_manifest(m)
        self.assertFalse(result["valid"])
        self.assertIn("RAW_RESPONSE_SAVED_MUST_BE_FALSE", result["blockers"])

    def test_validate_blocks_base64_emitted(self):
        m = SingleQwenRequestManifest(base64_emitted=True)
        result = validate_request_manifest(m)
        self.assertFalse(result["valid"])
        self.assertIn("BASE64_EMITTED_MUST_BE_FALSE", result["blockers"])

    def test_build_from_manifest_and_roi(self):
        m = build_request_manifest(self.manifest, self.roi)
        self.assertFalse(m.real_api_allowed)
        self.assertTrue(m.check_only)
        self.assertFalse(m.raw_response_saved)
        self.assertFalse(m.base64_emitted)

    def test_forbidden_fields_rejected(self):
        with self.assertRaises(ValueError):
            SingleQwenRequestManifest.from_dict({"api_key": "sk-test"})

    def test_forbidden_base64_field_rejected(self):
        with self.assertRaises(ValueError):
            SingleQwenRequestManifest.from_dict({"base64": "abcdef"})

    def test_request_id_generated(self):
        m = build_request_manifest(self.manifest, self.roi)
        self.assertTrue(len(m.request_id) > 0)
        self.assertEqual(len(m.request_id), 12)


if __name__ == "__main__":
    unittest.main()
