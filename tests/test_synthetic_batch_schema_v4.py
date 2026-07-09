import json
import unittest
from copy import deepcopy
from pathlib import Path

from app.recognition.synthetic_batch_schema import SyntheticBatchFixture


FIXTURE = Path("tests/fixtures/recognition/synthetic_batches/batch_all_clear.json")


class SyntheticBatchSchemaV4Tests(unittest.TestCase):
    def load_data(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_valid_fixture_loads(self):
        fixture = SyntheticBatchFixture.from_dict(self.load_data())
        self.assertEqual(fixture.schema_version, 4)

    def test_missing_batch_id_fails(self):
        data = self.load_data()
        data.pop("batch_id")
        with self.assertRaises(ValueError):
            SyntheticBatchFixture.from_dict(data)

    def test_missing_expected_fails(self):
        data = self.load_data()
        data.pop("expected")
        with self.assertRaises(ValueError):
            SyntheticBatchFixture.from_dict(data)

    def test_missing_students_fails(self):
        data = self.load_data()
        data.pop("students")
        with self.assertRaises(ValueError):
            SyntheticBatchFixture.from_dict(data)

    def test_missing_items_fails(self):
        data = self.load_data()
        data.pop("items")
        with self.assertRaises(ValueError):
            SyntheticBatchFixture.from_dict(data)

    def test_qwen_budget_missing_uses_safe_default(self):
        data = self.load_data()
        data.pop("qwen_budget")
        fixture = SyntheticBatchFixture.from_dict(data)
        self.assertFalse(fixture.qwen_budget["enabled"])

    def test_invalid_expected_type_fails(self):
        data = self.load_data()
        data["expected"] = []
        with self.assertRaises(ValueError):
            SyntheticBatchFixture.from_dict(data)

    def test_json_round_trip_stable(self):
        fixture = SyntheticBatchFixture.from_dict(self.load_data())
        self.assertEqual(fixture.to_dict(), SyntheticBatchFixture.from_dict(fixture.to_dict()).to_dict())


if __name__ == "__main__":
    unittest.main()
