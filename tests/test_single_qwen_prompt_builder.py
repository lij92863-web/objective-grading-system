"""Tests for single Qwen prompt builder — R364."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.qwen_adapter.single_prompt_builder import build_single_qwen_prompt


class SingleQwenPromptBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_single_image_manifest(
            "tests/fixtures/recognition/single_image/demo_single_image_manifest.json")
        cls.roi = load_manual_roi_file(
            "tests/fixtures/recognition/single_image/demo_manual_roi.json")

    def test_prompt_contains_json_instruction(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        self.assertIn("JSON", result["prompt_text"])

    def test_prompt_no_api_key(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        self.assertNotIn("sk-", result["prompt_text"])
        self.assertNotIn("Bearer ", result["prompt_text"])

    def test_prompt_no_base64(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        self.assertNotIn("data:image", result["prompt_text"])
        self.assertNotIn("base64", result["prompt_text"].lower())

    def test_prompt_no_full_local_path(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        self.assertNotIn("C:\\", result["prompt_text"])
        self.assertNotIn("/home/", result["prompt_text"])
        self.assertNotIn("/Users/", result["prompt_text"])

    def test_prompt_forbids_scoring(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        text = result["prompt_text"]
        self.assertTrue(
            "不判分" in text or "不要判分" in text or "no score" in text.lower() or
            "do not score" in text.lower()
        )

    def test_prompt_forbids_identity_confirmation(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        text = result["prompt_text"]
        self.assertTrue("candidate" in text.lower())

    def test_prompt_forbids_creating_question_ids(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        text = result["prompt_text"]
        self.assertTrue("不得自造" in text or "不要自造" in text or
                        "given question_id" in text.lower())

    def test_prompt_has_expected_schema(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        schema = result["expected_json_schema"]
        self.assertIn("properties", schema)
        self.assertIn("items", schema.get("required", []))

    def test_summary_fields(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        summary = result["summary"]
        self.assertTrue(summary["forbids_scoring"])
        self.assertTrue(summary["forbids_identity_confirmation"])

    def test_warnings_on_suspicious_content(self):
        result = build_single_qwen_prompt(self.manifest, self.roi)
        self.assertNotIn("PROMPT_CONTAINS_SECRET", result["warnings"])
        self.assertNotIn("PROMPT_CONTAINS_BASE64", result["warnings"])


if __name__ == "__main__":
    unittest.main()
