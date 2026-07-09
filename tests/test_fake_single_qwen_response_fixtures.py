"""Tests for fake single Qwen response fixtures — R367."""
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

FIXTURE_DIR = Path("tests/fixtures/recognition/qwen_single_response")


class FakeSingleQwenResponseFixtureTests(unittest.TestCase):
    def _load_json(self, name):
        path = FIXTURE_DIR / name
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_text(self, name):
        path = FIXTURE_DIR / name
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_valid_fixture_loads(self):
        data = self._load_json("fake_single_qwen_valid_choice_blank_identity.json")
        self.assertIn("items", data)
        self.assertGreater(len(data["items"]), 0)
        meta = data.get("_fixture_meta", {})
        self.assertTrue(meta.get("is_fake"))
        self.assertFalse(meta.get("contains_real_student_data"))
        self.assertFalse(meta.get("contains_api_key"))
        self.assertFalse(meta.get("contains_base64"))

    def test_valid_fixture_no_real_info(self):
        data = self._load_json("fake_single_qwen_valid_choice_blank_identity.json")
        raw = json.dumps(data)
        self.assertNotIn("sk-", raw)
        self.assertNotIn("data:image", raw)
        self.assertNotIn("Bearer ", raw)

    def test_invalid_option_fixture(self):
        data = self._load_json("fake_single_qwen_invalid_option.json")
        items = data.get("items", [])
        has_invalid = any(
            item.get("invalid_option") or
            item.get("answer", "") not in ("", "A", "B", "C", "D", "AB", "blank", "unclear")
            for item in items
        )
        self.assertTrue(has_invalid or len(items) > 0)
        meta = data.get("_fixture_meta", {})
        self.assertFalse(meta.get("contains_real_student_data"))

    def test_low_confidence_fixture(self):
        data = self._load_json("fake_single_qwen_low_confidence_blank.json")
        items = data.get("items", [])
        has_low = any(item.get("confidence", 1.0) < 0.80 for item in items)
        self.assertTrue(has_low)
        self.assertFalse(data.get("_fixture_meta", {}).get("contains_api_key"))

    def test_identity_fixture(self):
        data = self._load_json("fake_single_qwen_identity_candidate.json")
        self.assertIn("identity_candidate", data)
        self.assertFalse(data.get("_fixture_meta", {}).get("contains_real_student_data"))

    def test_extra_question_id_fixture(self):
        data = self._load_json("fake_single_qwen_extra_question_id.json")
        items = data.get("items", [])
        ids = [item.get("question_id", "") for item in items]
        self.assertIn("Q99", ids)

    def test_missing_question_id_fixture(self):
        data = self._load_json("fake_single_qwen_missing_question_id.json")
        items = data.get("items", [])
        has_missing = any(not item.get("question_id") for item in items)
        self.assertTrue(has_missing)

    def test_malformed_fixture_is_not_valid_json(self):
        text = self._load_text("fake_single_qwen_malformed_json.txt")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(text)

    def test_all_fixtures_no_api_key(self):
        for name in FIXTURE_DIR.glob("*.json"):
            data = self._load_json(name.name)
            raw = json.dumps(data)
            self.assertNotIn("sk-", raw, f"{name.name} contains sk- pattern")
            self.assertNotIn("data:image", raw, f"{name.name} contains data:image")
            self.assertNotIn("Bearer ", raw, f"{name.name} contains Bearer")

    def test_all_fixtures_no_real_student_data(self):
        for name in FIXTURE_DIR.glob("*.json"):
            data = self._load_json(name.name)
            meta = data.get("_fixture_meta", {})
            self.assertFalse(
                meta.get("contains_real_student_data", True),
                f"{name.name} claims real student data"
            )


if __name__ == "__main__":
    unittest.main()
