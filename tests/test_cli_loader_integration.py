"""CLI smoke after workflow CSV loader cutover."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class CliLoaderIntegrationTests(unittest.TestCase):
    def test_cli_demo_outputs_after_loader_cutover(self):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo samples")
        temp_dir = Path(tempfile.mkdtemp(prefix="l7d_cli_", dir=PROJECT_ROOT / "data"))
        try:
            out = temp_dir / "out"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "objective_grader.py"),
                    "--answer-key",
                    str(DEMO_KEY),
                    "--submissions",
                    str(DEMO_SUB),
                    "--out-dir",
                    str(out),
                    "--no-archive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            for filename in (
                "summary.csv",
                "detail.csv",
                "item_analysis.csv",
                "knowledge_profile.csv",
                "practice_recommendations.csv",
                "class_report.csv",
                "validation_report.csv",
                "student_report.csv",
                "exam_report.xlsx",
                "simple_score_report.xlsx",
                "simple_report.html",
                "advanced_dashboard.html",
                "index.html",
            ):
                self.assertTrue((out / filename).exists(), filename)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
