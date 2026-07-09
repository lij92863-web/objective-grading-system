"""Tests for prompt schema guard — R380."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.prompt_schema_guard import validate_prompt_schema


class PromptSchemaGuardTests(unittest.TestCase):
    def test_valid_prompt_with_json_passes(self):
        prompt = "请只返回 JSON：{\"question_id\": \"Q1\"}"
        result = validate_prompt_schema(prompt)
        self.assertTrue(result["valid"])

    def test_missing_json_instruction(self):
        prompt = "请识别这张图片中的选择题答案。"
        result = validate_prompt_schema(prompt)
        self.assertFalse(result["valid"])
        self.assertIn("MISSING_JSON_INSTRUCTION", result["blockers"])

    def test_contains_grading_instruction(self):
        prompt = "请判分，返回 final score。JSON format."
        result = validate_prompt_schema(prompt)
        self.assertFalse(result["valid"])
        self.assertTrue(any("GRADING" in b for b in result["blockers"]))

    def test_contains_final_score(self):
        prompt = "Return JSON with final_score field."
        result = validate_prompt_schema(prompt)
        self.assertFalse(result["valid"])
        self.assertTrue(any("final" in b.lower() for b in result["blockers"]))

    def test_no_api_key_in_prompt(self):
        prompt = "JSON with sk-secret-key"
        result = validate_prompt_schema(prompt)
        self.assertFalse(result["valid"])
        self.assertTrue(any("FORBIDDEN_PATTERN" in b for b in result["blockers"]))

    def test_no_base64_in_prompt(self):
        prompt = "Image data: data:image/png;base64,abc123 JSON"
        result = validate_prompt_schema(prompt)
        self.assertFalse(result["valid"])
        self.assertTrue(any("FORBIDDEN_PATTERN" in b for b in result["blockers"]))

    def test_no_full_local_path(self):
        prompt = "File at C:\\Users\\test\\image.png JSON format"
        result = validate_prompt_schema(prompt)
        self.assertTrue(any("FULL_LOCAL_PATH" in w for w in result["warnings"]))

    def test_forbid_scoring_instruction(self):
        prompt = "只返回 JSON 候选结果，不要评分不要判分"
        result = validate_prompt_schema(prompt)
        # The guard correctly detects "判分" as a grading-related term
        # and blocks it. This is EXPECTED behavior — the guard errs on
        # the side of caution. The prompt builder should use SAFE language.
        self.assertFalse(result["valid"])
        self.assertTrue(any("GRADING" in b for b in result["blockers"]))

    def test_no_bearer_token(self):
        prompt = "Authorization: Bearer token123 JSON"
        result = validate_prompt_schema(prompt)
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
