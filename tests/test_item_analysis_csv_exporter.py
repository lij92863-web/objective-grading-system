"""Item-analysis CSV exporter tests — Stage E2C."""

import ast
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples" / "demo_exam" / "answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples" / "demo_exam" / "submissions_sample.csv"


class ItemAnalysisCsvExporterTests(unittest.TestCase):
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
            exam_name="test_e2c",
        )

    def _read_csv_rows(self, path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8-sig", newline="") as h:
            return list(csv.DictReader(h))

    # -- field order --------------------------------------------------------

    def test_field_order_matches_legacy(self):
        from app.infrastructure.exporters.item_analysis_csv_exporter import \
            ITEM_ANALYSIS_FIELDNAMES

        tmp = tempfile.mkdtemp(prefix="e2c_", dir=PROJECT_ROOT / "data")
        legacy_dir = Path(tmp) / "legacy"
        try:
            self._run_legacy_grading(legacy_dir)
            with (legacy_dir / "item_analysis.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as h:
                legacy_fields = csv.DictReader(h).fieldnames
            self.assertEqual(
                list(ITEM_ANALYSIS_FIELDNAMES), legacy_fields,
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- round-trip ---------------------------------------------------------

    def test_round_trip_matches_legacy(self):
        from app.infrastructure.exporters.item_analysis_csv_exporter import \
            ItemAnalysisCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2c_", dir=PROJECT_ROOT / "data")
        try:
            legacy_dir = Path(tmp) / "legacy"
            self._run_legacy_grading(legacy_dir)
            legacy_rows = self._read_csv_rows(legacy_dir / "item_analysis.csv")

            new_dir = Path(tmp) / "new"; new_dir.mkdir()
            exporter = ItemAnalysisCsvExporter()
            result = exporter.export(
                ExportRequest(output_dir=new_dir), legacy_rows
            )
            self.assertEqual(result.status, "ok")
            self.assertIn("item_analysis.csv", result.generated_files)

            new_rows = self._read_csv_rows(new_dir / "item_analysis.csv")
            self.assertEqual(len(new_rows), len(legacy_rows))
            self.assertEqual(new_rows[0], legacy_rows[0])
            self.assertEqual(new_rows[-1], legacy_rows[-1])
            for row in new_rows:
                self.assertIn("question", row)
                self.assertIn("accuracy", row)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- encoding -----------------------------------------------------------

    def test_encoding_utf8_bom(self):
        from app.infrastructure.exporters.item_analysis_csv_exporter import \
            ItemAnalysisCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2c_", dir=PROJECT_ROOT / "data")
        try:
            legacy_dir = Path(tmp) / "legacy"
            self._run_legacy_grading(legacy_dir)
            legacy_rows = self._read_csv_rows(legacy_dir / "item_analysis.csv")
            new_dir = Path(tmp) / "new"; new_dir.mkdir()
            ItemAnalysisCsvExporter().export(
                ExportRequest(output_dir=new_dir), legacy_rows
            )
            raw = (new_dir / "item_analysis.csv").read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            rows = self._read_csv_rows(new_dir / "item_analysis.csv")
            self.assertFalse(rows[0].get("﻿question"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- empty rows ----------------------------------------------------------

    def test_empty_rows_writes_header_with_warning(self):
        from app.infrastructure.exporters.item_analysis_csv_exporter import \
            ItemAnalysisCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest

        tmp = tempfile.mkdtemp(prefix="e2c_", dir=PROJECT_ROOT / "data")
        try:
            out_dir = Path(tmp)
            result = ItemAnalysisCsvExporter().export(
                ExportRequest(output_dir=out_dir), []
            )
            self.assertEqual(result.status, "ok")
            self.assertIn("item_analysis_rows_empty", result.warnings)
            rows = self._read_csv_rows(out_dir / "item_analysis.csv")
            self.assertEqual(len(rows), 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- no legacy -----------------------------------------------------------

    def test_exporter_does_not_import_legacy(self):
        f = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "item_analysis_csv_exporter.py"
        )
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", "") or ""
                for alias in node.names:
                    name = f"{mod}.{alias.name}" if mod else alias.name
                    self.assertFalse(
                        name.startswith("legacy"),
                        f"imports legacy: {name}",
                    )

    def test_legacy_behavior_still_passes(self):
        tmp = tempfile.mkdtemp(prefix="e2c_", dir=PROJECT_ROOT / "data")
        try:
            result = self._run_legacy_grading(Path(tmp))
            self.assertTrue(result["ok"])
            self.assertTrue((Path(tmp) / "item_analysis.csv").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
