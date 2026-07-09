import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from legacy import objective_grader_legacy as legacy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
FIELDNAMES = ["severity", "scope", "item", "message"]


class ValidationErrorPathBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists() or not DEMO_SUB.exists():
            raise unittest.SkipTest("demo samples are unavailable")

    def _read_rows(self, path):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return reader.fieldnames, list(reader)

    def test_legacy_writer_field_order_and_content(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="l8a_writer_", dir=PROJECT_ROOT / "data"))
        try:
            rows = [
                {
                    "severity": "error",
                    "scope": "input",
                    "item": "学生甲",
                    "message": "缺少答题记录",
                }
            ]
            out_path = temp_dir / "validation_report.csv"
            legacy.write_validation_report(out_path, rows)

            fieldnames, written_rows = self._read_rows(out_path)
            self.assertEqual(fieldnames, FIELDNAMES)
            self.assertEqual(written_rows, rows)
            self.assertTrue(out_path.read_bytes().startswith(b"\xef\xbb\xbf"))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_legacy_writer_empty_rows_keeps_header(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="l8a_empty_", dir=PROJECT_ROOT / "data"))
        try:
            out_path = temp_dir / "validation_report.csv"
            legacy.write_validation_report(out_path, [])

            fieldnames, written_rows = self._read_rows(out_path)
            self.assertEqual(fieldnames, FIELDNAMES)
            self.assertEqual(written_rows, [])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_workflow_blocking_error_path_writes_validation_report(self):
        from app.workflow import run_grading

        temp_dir = Path(tempfile.mkdtemp(prefix="l8a_workflow_", dir=PROJECT_ROOT / "data"))
        try:
            out_dir = temp_dir / "out"
            result = run_grading(
                DEMO_KEY,
                DEMO_SUB,
                out_dir,
                no_archive=True,
                exam_name="l8a",
                extra_validation_rows=[
                    {
                        "severity": "error",
                        "scope": "input",
                        "item": "manual",
                        "message": "forced blocking error",
                    }
                ],
            )

            self.assertFalse(result["ok"])
            self.assertTrue(result["blocked"])
            validation_path = out_dir / "validation_report.csv"
            self.assertTrue(validation_path.exists())
            self.assertTrue((out_dir / "error_report.html").exists())
            fieldnames, rows = self._read_rows(validation_path)
            self.assertEqual(fieldnames, FIELDNAMES)
            self.assertIn("forced blocking error", [row["message"] for row in rows])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

