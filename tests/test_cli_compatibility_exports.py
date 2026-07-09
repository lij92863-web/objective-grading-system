import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import objective_grader


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CliCompatibilityExportsTests(unittest.TestCase):
    def test_common_legacy_symbols_still_exported(self):
        expected = [
            "AnswerKey",
            "QuestionSpec",
            "Submission",
            "grade_all",
            "load_answer_key",
            "load_submissions",
            "create_sample_files",
            "write_summary",
        ]
        for name in expected:
            self.assertTrue(hasattr(objective_grader, name), name)

    def test_cli_arguments_still_available(self):
        parser = objective_grader.build_parser()
        option_strings = {
            option
            for action in parser._actions
            for option in action.option_strings
        }
        for option in [
            "--answer-key",
            "--submissions",
            "--question-bank",
            "--out-dir",
            "--make-samples",
            "--weak-threshold",
            "--practice-per-tag",
            "--exam-name",
            "--class-name",
            "--subject",
            "--exam-date",
            "--archive-root",
            "--no-archive",
            "--allow-errors",
        ]:
            self.assertIn(option, option_strings)

    def test_make_samples_cli_still_works(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="l11b_cli_", dir=PROJECT_ROOT / "data"))
        try:
            out_dir = temp_dir / "samples"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "objective_grader.py"),
                    "--make-samples",
                    "--out-dir",
                    str(out_dir),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "answer_key_sample.csv").exists())
            self.assertTrue((out_dir / "submissions_sample.csv").exists())
            self.assertTrue((out_dir / "question_bank_sample.csv").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
