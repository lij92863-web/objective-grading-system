import tempfile
import unittest
from pathlib import Path

from app.recognition.synthetic_batch_loader import (
    load_all_fixtures,
    load_fixture_by_path,
    load_fixture_by_scenario,
)


class SyntheticBatchLoaderTests(unittest.TestCase):
    def test_load_by_path(self):
        fixture = load_fixture_by_path("tests/fixtures/recognition/synthetic_batches/batch_all_clear.json")
        self.assertEqual(fixture.scenario, "all_clear")

    def test_load_by_scenario(self):
        fixture = load_fixture_by_scenario("with_review")
        self.assertEqual(fixture.scenario, "with_review")

    def test_unknown_scenario_fails(self):
        with self.assertRaises(ValueError):
            load_fixture_by_scenario("unknown")

    def test_invalid_json_fails(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as handle:
            handle.write("{")
            path = handle.name
        with self.assertRaises(ValueError):
            load_fixture_by_path(path)
        Path(path).unlink()

    def test_missing_expected_fails(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as handle:
            handle.write('{"schema_version":4,"batch_id":"x"}')
            path = handle.name
        with self.assertRaises(ValueError):
            load_fixture_by_path(path)
        Path(path).unlink()

    def test_all_known_scenarios_load(self):
        self.assertEqual(len(load_all_fixtures()), 8)


if __name__ == "__main__":
    unittest.main()
