"""Tests for SingleQwenTrialConfig — R362."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.qwen_adapter.single_trial_config import (
    SingleQwenTrialConfig,
    validate_single_qwen_trial_config,
    safe_config_summary,
    load_single_qwen_trial_config,
)


class SingleQwenTrialConfigTests(unittest.TestCase):
    def test_default_fail_closed(self):
        config = SingleQwenTrialConfig()
        self.assertTrue(config.check_only)
        self.assertFalse(config.allow_real_api)

    def test_allow_real_api_false_by_default(self):
        config = SingleQwenTrialConfig()
        self.assertFalse(config.allow_real_api)
        result = validate_single_qwen_trial_config(config)
        self.assertTrue(result["valid"])

    def test_save_raw_response_true_invalid(self):
        config = SingleQwenTrialConfig(save_raw_response=True)
        result = validate_single_qwen_trial_config(config)
        self.assertFalse(result["valid"])
        self.assertIn("SAVE_RAW_RESPONSE_MUST_BE_FALSE", result["blockers"])

    def test_emit_base64_true_invalid(self):
        config = SingleQwenTrialConfig(emit_base64=True)
        result = validate_single_qwen_trial_config(config)
        self.assertFalse(result["valid"])
        self.assertIn("EMIT_BASE64_MUST_BE_FALSE", result["blockers"])

    def test_api_key_env_suspicious_value_invalid(self):
        config = SingleQwenTrialConfig(api_key_env="sk-abcdefghijklmnopqrstuvwxyz")
        result = validate_single_qwen_trial_config(config)
        self.assertFalse(result["valid"])
        key_blockers = [b for b in result["blockers"] if "API_KEY" in b or "SUSPICIOUS" in b]
        self.assertTrue(len(key_blockers) > 0)

    def test_api_key_env_too_long_looks_like_value(self):
        config = SingleQwenTrialConfig(api_key_env="a" * 51)
        result = validate_single_qwen_trial_config(config)
        self.assertFalse(result["valid"])

    def test_check_only_does_not_need_key(self):
        config = SingleQwenTrialConfig(check_only=True, api_key_env="")
        result = validate_single_qwen_trial_config(config)
        self.assertTrue(result["valid"])

    def test_real_api_requires_explicit_allow(self):
        config = SingleQwenTrialConfig(allow_real_api=False)
        self.assertFalse(config.allow_real_api)

    def test_json_round_trip(self):
        config = SingleQwenTrialConfig(
            manifest_path="tests/fixtures/recognition/single_image/demo_single_image_manifest.json",
            roi_path="tests/fixtures/recognition/single_image/demo_manual_roi.json",
        )
        d = config.to_dict()
        config2 = SingleQwenTrialConfig.from_dict(d)
        self.assertEqual(config.check_only, config2.check_only)
        self.assertEqual(config.allow_real_api, config2.allow_real_api)
        self.assertEqual(config.manifest_path, config2.manifest_path)

    def test_safe_summary_no_secrets(self):
        config = SingleQwenTrialConfig(api_key_env="MY_KEY_VAR")
        summary = safe_config_summary(config)
        self.assertTrue(summary["api_key_env_present"])
        self.assertNotIn("MY_KEY_VAR", json.dumps(summary))
        raw = json.dumps(summary)
        self.assertNotIn("sk-", raw)

    def test_max_calls_exceeds_one_blocks(self):
        config = SingleQwenTrialConfig(max_calls=2)
        result = validate_single_qwen_trial_config(config)
        self.assertFalse(result["valid"])
        self.assertIn("MAX_CALLS_EXCEEDS_ONE", result["blockers"])

    def test_require_anonymous_false_blocks(self):
        config = SingleQwenTrialConfig(require_anonymous=False)
        result = validate_single_qwen_trial_config(config)
        self.assertFalse(result["valid"])
        self.assertIn("REQUIRE_ANONYMOUS_MUST_BE_TRUE", result["blockers"])

    def test_require_manual_roi_false_blocks(self):
        config = SingleQwenTrialConfig(require_manual_roi=False)
        result = validate_single_qwen_trial_config(config)
        self.assertFalse(result["valid"])
        self.assertIn("REQUIRE_MANUAL_ROI_MUST_BE_TRUE", result["blockers"])

    def test_load_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            config = SingleQwenTrialConfig(check_only=True, allow_real_api=False)
            path.write_text(json.dumps(config.to_dict()), encoding="utf-8")
            loaded = load_single_qwen_trial_config(path)
            self.assertTrue(loaded.check_only)
            self.assertFalse(loaded.allow_real_api)


if __name__ == "__main__":
    unittest.main()
