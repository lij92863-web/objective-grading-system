"""Detail CSV exporter tests — Stage E2B.

Verifies the new DetailCsvExporter produces output compatible with
legacy write_detail.
"""

import ast
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples" / "demo_exam" / "answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples" / "demo_exam" / "submissions_sample.csv"


class DetailCsvExporterTests(unittest.TestCase):
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
            exam_name="test_e2b",
        )

    def _read_csv_rows(self, path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8-sig", newline="") as h:
            return list(csv.DictReader(h))

    # -- field order --------------------------------------------------------

    def test_field_order_matches_legacy(self):
        from app.infrastructure.exporters.detail_csv_exporter import \
            DETAIL_FIELDNAMES

        tmp = tempfile.mkdtemp(prefix="e2b_order_", dir=PROJECT_ROOT / "data")
        legacy_dir = Path(tmp) / "legacy"
        try:
            self._run_legacy_grading(legacy_dir)
            with (legacy_dir / "detail.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as h:
                legacy_fields = csv.DictReader(h).fieldnames

            self.assertEqual(
                list(DETAIL_FIELDNAMES), legacy_fields,
                f"DETAIL_FIELDNAMES mismatch: "
                f"new={DETAIL_FIELDNAMES}, legacy={legacy_fields}",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- content round-trip -------------------------------------------------

    def test_round_trip_matches_legacy(self):
        from app.infrastructure.exporters.detail_csv_exporter import \
            DetailCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2b_rt_", dir=PROJECT_ROOT / "data")
        try:
            legacy_dir = Path(tmp) / "legacy"
            self._run_legacy_grading(legacy_dir)
            legacy_rows = self._read_csv_rows(legacy_dir / "detail.csv")

            new_dir = Path(tmp) / "new"; new_dir.mkdir()
            exporter = DetailCsvExporter()
            result = exporter.export(
                ExportRequest(output_dir=new_dir), legacy_rows
            )
            self.assertEqual(result.status, "ok")
            self.assertIn("detail.csv", result.generated_files)

            new_rows = self._read_csv_rows(new_dir / "detail.csv")
            self.assertEqual(len(new_rows), len(legacy_rows),
                             "Row count mismatch")
            # Check first row
            self.assertEqual(new_rows[0], legacy_rows[0])

            # Check last row
            self.assertEqual(new_rows[-1], legacy_rows[-1])

            # Key fields present
            for row in new_rows:
                self.assertIn("student_id", row)
                self.assertIn("question", row)
                self.assertIn("status", row)
                self.assertIn("score", row)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- encoding -----------------------------------------------------------

    def test_encoding_is_utf8_bom_and_no_field_pollution(self):
        from app.infrastructure.exporters.detail_csv_exporter import \
            DetailCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2b_enc_", dir=PROJECT_ROOT / "data")
        try:
            legacy_dir = Path(tmp) / "legacy"
            self._run_legacy_grading(legacy_dir)
            legacy_rows = self._read_csv_rows(legacy_dir / "detail.csv")

            new_dir = Path(tmp) / "new"; new_dir.mkdir()
            DetailCsvExporter().export(
                ExportRequest(output_dir=new_dir), legacy_rows
            )

            raw = (new_dir / "detail.csv").read_bytes()
            self.assertTrue(
                raw.startswith(b"\xef\xbb\xbf"), "Missing UTF-8 BOM"
            )
            rows = self._read_csv_rows(new_dir / "detail.csv")
            self.assertFalse(
                rows[0].get("﻿student_id"),
                "BOM leaked into first field name",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- empty rows ----------------------------------------------------------

    def test_empty_rows_writes_header_only(self):
        from app.infrastructure.exporters.detail_csv_exporter import \
            DetailCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2b_empty_", dir=PROJECT_ROOT / "data")
        try:
            out_dir = Path(tmp)
            exporter = DetailCsvExporter()
            result = exporter.export(ExportRequest(output_dir=out_dir), [])
            self.assertEqual(result.status, "ok")
            self.assertIn("detail_rows_empty", result.warnings)
            rows = self._read_csv_rows(out_dir / "detail.csv")
            self.assertEqual(len(rows), 0, "Should have no data rows")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- no legacy import ---------------------------------------------------

    def test_exporter_does_not_import_legacy(self):
        f = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "detail_csv_exporter.py"
        )
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", "") or ""
                for alias in node.names:
                    name = f"{mod}.{alias.name}" if mod else alias.name
                    self.assertFalse(
                        name.startswith("legacy"),
                        f"detail_csv_exporter.py imports legacy: {name}",
                    )

    # -- old tests -----------------------------------------------------------

    def test_legacy_behavior_still_passes(self):
        tmp = tempfile.mkdtemp(prefix="e2b_old_", dir=PROJECT_ROOT / "data")
        try:
            result = self._run_legacy_grading(Path(tmp))
            self.assertTrue(result["ok"])
            self.assertTrue((Path(tmp) / "detail.csv").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
