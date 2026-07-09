"""R40C: Golden suite v2 tests."""
import json, unittest
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "recognition" / "golden_cases_v2"


class GoldenSuiteV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {}
        for d in sorted(FIXTURES.glob("case_*")):
            p = d / "payload.json"
            if p.exists(): cls.cases[d.name] = json.loads(p.read_text("utf-8"))

    def test_all_cases_exist(self):
        names = {"case_omr_high_confidence_choice","case_omr_ambiguous_choice",
                 "case_omr_qwen_agree","case_omr_qwen_conflict",
                 "case_qwen_malformed_response","case_blank_qwen_low_confidence",
                 "case_identity_duplicate_number","case_missing_roi_blocking",
                 "case_invalid_option_blocking","case_engine_error_blocking"}
        self.assertTrue(names.issubset(set(self.cases.keys())),
                        f"Missing: {names - set(self.cases.keys())}")

    def test_omr_agree_no_conflict(self):
        c = self.cases["case_omr_qwen_agree"]
        self.assertTrue(c["omr_qwen_agree"])

    def test_omr_conflict_needs_review(self):
        c = self.cases["case_omr_qwen_conflict"]
        self.assertTrue(c["omr_qwen_conflict"])

    def test_qwen_malformed_engine_error(self):
        c = self.cases["case_qwen_malformed_response"]
        self.assertTrue(c["malformed"])

    def test_blank_low_confidence_needs_review(self):
        c = self.cases["case_blank_qwen_low_confidence"]
        self.assertTrue(c["low_confidence"])

    def test_duplicate_identity_blocking(self):
        c = self.cases["case_identity_duplicate_number"]
        self.assertEqual(c["expected_status"], "blocking")

    def test_missing_roi_blocking(self):
        c = self.cases["case_missing_roi_blocking"]
        self.assertEqual(c["expected_status"], "blocking")

    def test_invalid_option_blocking(self):
        c = self.cases["case_invalid_option_blocking"]
        self.assertEqual(c["expected_status"], "blocking")


if __name__ == "__main__": unittest.main()
