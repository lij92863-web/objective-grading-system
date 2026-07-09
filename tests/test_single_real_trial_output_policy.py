"""Tests for single real trial output policy — R376."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_real_trial_output_policy import validate_output_path


class SingleRealTrialOutputPolicyTests(unittest.TestCase):
    def test_data_tmp_allowed(self):
        result = validate_output_path("data/tmp/test_abc123.json", request_id="abc123")
        self.assertTrue(result["valid"])

    def test_data_reports_forbidden(self):
        result = validate_output_path("data/reports/test.json")
        self.assertFalse(result["valid"])
        self.assertTrue(any("FORBIDDEN" in b for b in result["blockers"]))

    def test_csv_forbidden(self):
        result = validate_output_path("data/tmp/report.csv")
        self.assertFalse(result["valid"])
        self.assertTrue(any("FORMAL_REPORT" in b for b in result["blockers"]))

    def test_xlsx_forbidden(self):
        result = validate_output_path("data/tmp/report.xlsx")
        self.assertFalse(result["valid"])

    def test_html_forbidden(self):
        result = validate_output_path("data/tmp/report.html")
        self.assertFalse(result["valid"])

    def test_json_allowed(self):
        result = validate_output_path("data/tmp/test_abcdef.json", request_id="abcdef")
        self.assertTrue(result["valid"])

    def test_raw_response_filename_forbidden(self):
        result = validate_output_path("data/tmp/raw_response_test.json")
        self.assertFalse(result["valid"])
        self.assertTrue(any("RAW_RESPONSE" in b for b in result["blockers"]))

    def test_base64_filename_forbidden(self):
        result = validate_output_path("data/tmp/base64_output.json")
        self.assertFalse(result["valid"])
        self.assertTrue(any("BASE64" in b for b in result["blockers"]))

    def test_filename_should_include_request_id(self):
        result = validate_output_path("data/tmp/generic_output.json", request_id="abc123")
        self.assertTrue(any("REQUEST_ID" in w for w in result["warnings"]))

    def test_filename_with_request_id_ok(self):
        result = validate_output_path("data/tmp/result_abc123_sanitized.json", request_id="abc123")
        self.assertTrue(result["valid"])

    def test_exams_dir_forbidden(self):
        result = validate_output_path("data/exams/test.json")
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
