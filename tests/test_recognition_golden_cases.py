"""R17: Golden cases fixture tests."""
import json, unittest
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "recognition" / "golden_cases"


class RecognitionGoldenCasesTests(unittest.TestCase):
    def test_all_cases_exist(self):
        cases = ["auto_accept_choice","choice_conflict","blank_low_confidence",
                 "identity_confirmed","identity_conflict","missing_identity",
                 "invalid_option","engine_error"]
        for c in cases:
            self.assertTrue((FIXTURES/c/"payload.json").exists(), f"Missing {c}")

    def test_auto_accept_case(self):
        p = json.loads((FIXTURES/"auto_accept_choice/payload.json").read_text("utf-8"))
        self.assertEqual(p["1"]["expected_status"], "auto_accepted")
        self.assertFalse(p["1"]["expected_blocking"])

    def test_choice_conflict_case(self):
        p = json.loads((FIXTURES/"choice_conflict/payload.json").read_text("utf-8"))
        self.assertTrue(p.get("expected_conflict"))

    def test_blank_low_confidence_case(self):
        p = json.loads((FIXTURES/"blank_low_confidence/payload.json").read_text("utf-8"))
        self.assertEqual(p["7"]["expected_status"], "needs_review")

    def test_identity_confirmed_case(self):
        p = json.loads((FIXTURES/"identity_confirmed/payload.json").read_text("utf-8"))
        self.assertEqual(p["status"], "confirmed")
        self.assertFalse(p["expected_blocking"])

    def test_identity_conflict_case(self):
        p = json.loads((FIXTURES/"identity_conflict/payload.json").read_text("utf-8"))
        self.assertTrue(p["expected_blocking"])
        self.assertTrue(p["expected_confirmation_blocked"])

    def test_missing_identity_case(self):
        p = json.loads((FIXTURES/"missing_identity/payload.json").read_text("utf-8"))
        self.assertEqual(p["status"], "missing")
        self.assertTrue(p["expected_blocking"])

    def test_invalid_option_case(self):
        p = json.loads((FIXTURES/"invalid_option/payload.json").read_text("utf-8"))
        self.assertTrue(p["10"]["expected_blocking"])

    def test_engine_error_case(self):
        p = json.loads((FIXTURES/"engine_error/payload.json").read_text("utf-8"))
        self.assertEqual(p["1"]["expected_status"], "blocking")
        self.assertTrue(p["1"]["expected_blocking"])


if __name__ == "__main__": unittest.main()
