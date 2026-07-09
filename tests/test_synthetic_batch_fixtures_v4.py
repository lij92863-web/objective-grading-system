import unittest

from app.recognition.synthetic_batch_loader import load_all_fixtures
from app.recognition.synthetic_batch_schema import EXPECTED_FIELDS


class SyntheticBatchFixturesV4Tests(unittest.TestCase):
    def test_all_fixtures_load_and_have_expected_fields(self):
        fixtures = load_all_fixtures()
        self.assertEqual(len(fixtures), 8)
        for fixture in fixtures:
            self.assertTrue(EXPECTED_FIELDS.issubset(fixture.expected))
            self.assertGreaterEqual(len(fixture.students), 2)

    def test_required_risk_codes_present(self):
        by_scenario = {fixture.scenario: fixture for fixture in load_all_fixtures()}
        self.assertIn("identity_conflict", _codes(by_scenario["with_blocking_identity"]))
        self.assertIn("invalid_option", _codes(by_scenario["invalid_option"]))
        self.assertIn("missing_roi", _codes(by_scenario["missing_roi"]))
        self.assertIn("malformed_response", _codes(by_scenario["malformed_qwen_response"]))


def _codes(fixture):
    return {code for item in fixture.items for code in item["expected_exception_codes"]}


if __name__ == "__main__":
    unittest.main()
