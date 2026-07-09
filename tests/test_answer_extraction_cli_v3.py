from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_V3 = ROOT / "tests" / "fixtures" / "answer_extraction" / "document_models_v3"
SCRIPT = ROOT / "scripts" / "extract_answer_key.py"
FIXTURE_V2 = ROOT / "tests" / "fixtures" / "answer_extraction" / "document_models_v2"


def run_cli(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + list(args),
        capture_output=True, text=True, cwd=str(ROOT),
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, data


class AnswerExtractionCliV3Tests(unittest.TestCase):
    def test_json_output_is_parseable(self):
        rc, data = run_cli("--file", str(FIXTURE_V2 / "type1_same_file_boxed_realistic.json"), "--json")
        self.assertIn("strategy", data)

    def test_show_evidence_includes_evidence_in_answers(self):
        rc, data = run_cli("--file", str(FIXTURE_V2 / "type1_same_file_boxed_realistic.json"),
                            "--json", "--show-evidence")
        for answer in data.get("answers", {}).values():
            self.assertIn("evidence_text", answer)
            self.assertTrue(answer["evidence_text"])

    def test_summary_only_no_full_answers(self):
        rc, data = run_cli("--file", str(FIXTURE_V2 / "type1_same_file_boxed_realistic.json"),
                            "--json", "--summary-only")
        self.assertIn("strategy", data)
        self.assertNotIn("questions", data)

    def test_strict_on_accepted_returns_zero(self):
        rc, data = run_cli("--file", str(FIXTURE_V2 / "type1_same_file_boxed_realistic.json"),
                            "--json", "--strict")
        self.assertEqual(rc, 0)

    def test_type2_itemized_with_brackets_json(self):
        rc, data = run_cli("--file", str(FIXTURE_V2 / "type2_same_file_itemized_with_chinese_brackets.json"), "--json")
        self.assertEqual(data["strategy"], "same_file_itemized")

    def test_type3_split_boxed_json(self):
        rc, data = run_cli(
            "--question", str(FIXTURE_V2 / "type3_split_boxed_segmented_table_question.json"),
            "--answer", str(FIXTURE_V2 / "type3_split_boxed_segmented_table_answer.json"),
            "--json")
        self.assertEqual(data["strategy"], "split_file_boxed")

    def test_type4_split_itemized_with_empty_grid(self):
        rc, data = run_cli(
            "--question", str(FIXTURE_V2 / "type4_question_with_empty_grid_realistic.json"),
            "--answer", str(FIXTURE_V2 / "type4_answer_itemized_realistic.json"),
            "--json", "--show-evidence")
        self.assertEqual(data["strategy"], "split_file_itemized")
        self.assertTrue(data["report"]["ignored_student_answer_grid_count"] >= 1)

    def test_v3_real_chinese_brackets(self):
        fixture = FIXTURE_V3 / "type2_same_file_itemized_with_real_chinese_brackets.json"
        if fixture.exists():
            rc, data = run_cli("--file", str(fixture), "--json", "--show-evidence")
            self.assertIn("strategy", data)

    def test_missing_file_handled(self):
        rc, data = run_cli("--file", "nonexistent_file.json", "--json")
        self.assertIn("status", data)

    def test_accepted_answers_have_evidence_with_show_evidence(self):
        rc, data = run_cli("--file", str(FIXTURE_V2 / "type1_same_file_boxed_realistic.json"),
                            "--json", "--show-evidence")
        for qno, answer in data.get("answers", {}).items():
            if answer.get("validation_status") in ("accepted", "accepted_with_warnings"):
                self.assertTrue(answer.get("evidence_text"), f"Q{qno} accepted but no evidence")


if __name__ == "__main__":
    unittest.main()
