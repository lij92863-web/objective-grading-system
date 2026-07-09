from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "answer_extraction" / "document_models_v3" / "type2_same_file_itemized_with_real_chinese_brackets.json"
SCRIPT = ROOT / "scripts" / "extract_answer_key.py"


def run_cli(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + list(args),
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return result.returncode, json.loads(result.stdout)


class CliRealChineseBracketsEvidenceP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FIXTURE.exists():
            raise unittest.SkipTest(f"Fixture not found: {FIXTURE}")

    def test_cli_status_is_accepted_or_warnings(self):
        rc, data = run_cli("--file", str(FIXTURE), "--json", "--show-evidence")
        self.assertIn(data["status"], ("accepted", "accepted_with_warnings"))

    def test_answer_count_positive(self):
        rc, data = run_cli("--file", str(FIXTURE), "--json", "--show-evidence")
        self.assertGreater(data["answer_count"], 0)

    def test_accepted_answers_have_non_empty_evidence(self):
        rc, data = run_cli("--file", str(FIXTURE), "--json", "--show-evidence")
        for qno, answer in data.get("answers", {}).items():
            if answer.get("validation_status") in ("accepted", "accepted_with_warnings"):
                self.assertTrue(answer.get("evidence_text"),
                                f"Q{qno} accepted but evidence_text empty")

    def test_at_least_one_evidence_contains_real_bracket(self):
        rc, data = run_cli("--file", str(FIXTURE), "--json", "--show-evidence")
        found = False
        for answer in data.get("answers", {}).values():
            if "【答案】" in str(answer.get("evidence_text", "")):
                found = True
                break
        self.assertTrue(found, "No evidence_text contains 【答案】 in CLI output")

    def test_stdout_does_not_only_contain_compat_brackets(self):
        rc, data = run_cli("--file", str(FIXTURE), "--json", "--show-evidence")
        raw = json.dumps(data, ensure_ascii=False)
        self.assertIn("【答案】", raw, "CLI output must contain real bracket 【答案】")

    def test_accepted_with_warnings_also_has_evidence(self):
        rc, data = run_cli("--file", str(FIXTURE), "--json", "--show-evidence")
        for qno, answer in data.get("answers", {}).items():
            if answer.get("validation_status") == "accepted_with_warnings":
                self.assertTrue(answer.get("evidence_text"),
                                f"Q{qno} accepted_with_warnings but no evidence")


if __name__ == "__main__":
    unittest.main()
