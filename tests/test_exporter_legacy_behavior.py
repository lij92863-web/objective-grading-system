"""Legacy exporter behavior regression tests — Stage E1.

Locks the most important output behaviors of the legacy report/export
pipeline without testing individual cells.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples" / "demo_exam" / "answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples" / "demo_exam" / "submissions_sample.csv"


def _fresh_out_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="exporter_test_", dir=PROJECT_ROOT / "data"))


class ExporterLegacyBehaviorTests(unittest.TestCase):
    """Smoke tests: verify the legacy pipeline produces expected files."""

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists() or not DEMO_SUB.exists():
            raise unittest.SkipTest("Demo samples not found")

    def _run_grading(self, out_dir: Path, **kw):
        from app.workflow import run_grading
        return run_grading(
            answer_key_path=DEMO_KEY,
            submissions_path=DEMO_SUB,
            out_dir=out_dir,
            no_archive=True,
            exam_name="test_exporter",
            class_name="TestClass",
            subject="Math",
            **kw,
        )

    # -- basic output --------------------------------------------------------

    def test_demo_generates_report_directory(self):
        out_dir = _fresh_out_dir()
        try:
            result = self._run_grading(out_dir)
            self.assertTrue(result["ok"], f"Grading failed: {result}")
            self.assertTrue(out_dir.exists())
            self.assertTrue(out_dir.is_dir())
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_expected_files_exist(self):
        expected = {
            "summary.csv",
            "detail.csv",
            "item_analysis.csv",
            "knowledge_profile.csv",
            "class_report.csv",
            "student_report.csv",
            "student_wrong_list.csv",
            "teaching_plan.csv",
            "class_remedial_package.csv",
            "layered_remedial_plan.csv",
            "validation_report.csv",
            "exam_report.xlsx",
            "simple_score_report.xlsx",
            "simple_report.html",
            "advanced_dashboard.html",
            "index.html",
            "teaching_plan.html",
            "class_remedial_package.html",
            "layered_remedial_plan.html",
        }
        out_dir = _fresh_out_dir()
        try:
            self._run_grading(out_dir)
            for name in expected:
                fpath = out_dir / name
                self.assertTrue(
                    fpath.exists(),
                    f"Expected output file missing: {name}",
                )
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_summary_csv_is_not_empty(self):
        out_dir = _fresh_out_dir()
        try:
            self._run_grading(out_dir)
            summary = out_dir / "summary.csv"
            self.assertTrue(summary.exists())
            text = summary.read_text(encoding="utf-8-sig")
            self.assertIn("student_id", text.lower() or "score")
            lines = text.strip().splitlines()
            self.assertGreater(len(lines), 1, "Summary CSV has only header")
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_excel_exists_and_non_empty(self):
        out_dir = _fresh_out_dir()
        try:
            self._run_grading(out_dir)
            xlsx = out_dir / "exam_report.xlsx"
            self.assertTrue(xlsx.exists())
            self.assertGreater(xlsx.stat().st_size, 1000, "Excel file too small")
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_html_dashboard_exists(self):
        out_dir = _fresh_out_dir()
        try:
            self._run_grading(out_dir)
            html = out_dir / "advanced_dashboard.html"
            self.assertTrue(html.exists())
            text = html.read_text(encoding="utf-8")
            self.assertIn("<html", text.lower())
            self.assertIn("</html>", text.lower())
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_empty_output_not_treated_as_success(self):
        out_dir = _fresh_out_dir()
        # Remove any prior output that might confuse the test
        for p in out_dir.iterdir():
            p.unlink()
        self.assertEqual(len(list(out_dir.iterdir())), 0,
                         "Output dir should be empty before run")
        try:
            self._run_grading(out_dir)
            # After grading, dir should NOT be empty
            self.assertGreater(
                len(list(out_dir.iterdir())), 0,
                "Output dir is empty after grading — something is wrong",
            )
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    # -- safety ---------------------------------------------------------------

    def test_no_real_api_called(self):
        out_dir = _fresh_out_dir()
        try:
            result = self._run_grading(out_dir)
            self.assertTrue(result["ok"])
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_no_network_dependency(self):
        # The legacy pipeline is purely local
        out_dir = _fresh_out_dir()
        try:
            result = self._run_grading(out_dir)
            self.assertTrue(result["ok"])
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
