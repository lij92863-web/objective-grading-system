"""Summary CSV exporter tests — Stage E2A.

Verifies the new SummaryCsvExporter produces output compatible with
legacy write_summary.
"""

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples" / "demo_exam" / "answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples" / "demo_exam" / "submissions_sample.csv"


class SummaryCsvExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists() or not DEMO_SUB.exists():
            raise unittest.SkipTest("Demo samples not found")

    def _run_legacy_grading(self, out_dir: Path):
        from app.workflow import run_grading
        return run_grading(
            answer_key_path=DEMO_KEY,
            submissions_path=DEMO_SUB,
            out_dir=out_dir,
            no_archive=True,
            exam_name="test_e2a",
        )

    def _read_csv_rows(self, path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8-sig", newline="") as h:
            return list(csv.DictReader(h))

    # -- field order --------------------------------------------------------

    def test_field_order_matches_legacy(self):
        from app.infrastructure.exporters.summary_csv_exporter import \
            SUMMARY_FIELDNAMES

        tmp = tempfile.mkdtemp(prefix="e2a_order_", dir=PROJECT_ROOT / "data")
        legacy_dir = Path(tmp) / "legacy"
        try:
            self._run_legacy_grading(legacy_dir)
            legacy_rows = self._read_csv_rows(legacy_dir / "summary.csv")
            self.assertGreater(len(legacy_rows), 0, "Legacy produced no rows")

            # Read legacy fieldnames from actual output
            with (legacy_dir / "summary.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as h:
                reader = csv.DictReader(h)
                legacy_fields = reader.fieldnames

            self.assertEqual(
                list(SUMMARY_FIELDNAMES), legacy_fields,
                f"SUMMARY_FIELDNAMES mismatch: "
                f"new={SUMMARY_FIELDNAMES}, legacy={legacy_fields}",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- content round-trip -------------------------------------------------

    def test_round_trip_matches_legacy(self):
        from app.infrastructure.exporters.summary_csv_exporter import \
            SummaryCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2a_rt_", dir=PROJECT_ROOT / "data")
        try:
            legacy_dir = Path(tmp) / "legacy"
            self._run_legacy_grading(legacy_dir)
            legacy_rows = self._read_csv_rows(legacy_dir / "summary.csv")

            # Feed legacy rows into new exporter
            new_dir = Path(tmp) / "new"
            new_dir.mkdir()
            exporter = SummaryCsvExporter()
            result = exporter.export(
                ExportRequest(output_dir=new_dir), legacy_rows
            )
            self.assertEqual(result.status, "ok")
            self.assertIn("summary.csv", result.generated_files)

            new_rows = self._read_csv_rows(new_dir / "summary.csv")
            self.assertEqual(len(new_rows), len(legacy_rows),
                             "Row count mismatch")
            self.assertEqual(new_rows[0], legacy_rows[0],
                             "First row content differs")

            # Check key fields exist
            for row in new_rows:
                self.assertIn("student_id", row)
                self.assertIn("score", row)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- encoding compatibility ----------------------------------------------

    def test_encoding_is_utf8_bom(self):
        from app.infrastructure.exporters.summary_csv_exporter import \
            SummaryCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2a_enc_", dir=PROJECT_ROOT / "data")
        try:
            legacy_dir = Path(tmp) / "legacy"
            self._run_legacy_grading(legacy_dir)
            legacy_rows = self._read_csv_rows(legacy_dir / "summary.csv")

            new_dir = Path(tmp) / "new"; new_dir.mkdir()
            exporter = SummaryCsvExporter()
            exporter.export(ExportRequest(output_dir=new_dir), legacy_rows)

            raw = (new_dir / "summary.csv").read_bytes()
            self.assertTrue(
                raw.startswith(b"\xef\xbb\xbf"),
                "New summary.csv missing UTF-8 BOM",
            )

            # No BOM pollution in field names
            rows = self._read_csv_rows(new_dir / "summary.csv")
            self.assertFalse(
                rows[0].get("﻿student_id"),
                "BOM leaked into field name",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- empty rows ----------------------------------------------------------

    def test_empty_rows_writes_header_only(self):
        from app.infrastructure.exporters.summary_csv_exporter import \
            SummaryCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2a_empty_", dir=PROJECT_ROOT / "data")
        try:
            out_dir = Path(tmp)
            exporter = SummaryCsvExporter()
            result = exporter.export(ExportRequest(output_dir=out_dir), [])
            self.assertEqual(result.status, "ok")
            self.assertIn("summary_rows_empty", result.warnings)

            raw = (out_dir / "summary.csv").read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"),
                            "Empty file still needs BOM")
            rows = self._read_csv_rows(out_dir / "summary.csv")
            self.assertEqual(len(rows), 0, "Should have no data rows")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- no legacy import ---------------------------------------------------

    def test_exporter_does_not_import_legacy(self):
        import ast
        f = (
            PROJECT_ROOT
            / "app"
            / "infrastructure"
            / "exporters"
            / "summary_csv_exporter.py"
        )
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", "") or ""
                for alias in node.names:
                    name = f"{mod}.{alias.name}" if mod else alias.name
                    self.assertFalse(
                        name.startswith("legacy"),
                        f"summary_csv_exporter.py imports legacy: {name}",
                    )

    # -- old tests still pass ------------------------------------------------

    def test_legacy_exporter_behavior_still_passes(self):
        """Sanity: the old exporter test still runs fine."""
        tmp = tempfile.mkdtemp(prefix="e2a_old_", dir=PROJECT_ROOT / "data")
        try:
            result = self._run_legacy_grading(Path(tmp))
            self.assertTrue(result["ok"])
            self.assertTrue((Path(tmp) / "summary.csv").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
