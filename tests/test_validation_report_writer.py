import ast
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from legacy import objective_grader_legacy as legacy

from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.validation_report_csv_exporter import (
    VALIDATION_REPORT_FIELDNAMES,
    ValidationReportCsvExporter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ValidationReportWriterTests(unittest.TestCase):
    def _write_legacy_and_new(self, rows):
        temp_dir = Path(tempfile.mkdtemp(prefix="l8b_writer_", dir=PROJECT_ROOT / "data"))
        legacy_dir = temp_dir / "legacy"
        new_dir = temp_dir / "new"
        legacy_dir.mkdir()
        new_dir.mkdir()
        legacy.write_validation_report(legacy_dir / "validation_report.csv", rows)
        result = ValidationReportCsvExporter().export(ExportRequest(output_dir=new_dir), rows)
        return temp_dir, legacy_dir / "validation_report.csv", new_dir / "validation_report.csv", result

    def _read_fieldnames(self, path):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return csv.DictReader(handle).fieldnames

    def test_regular_and_chinese_rows_match_legacy_bytes(self):
        rows = [
            {
                "severity": "error",
                "scope": "input",
                "item": "学生甲",
                "message": "缺少答题记录",
            },
            {
                "severity": "warning",
                "scope": "grading",
                "item": "S002",
                "message": "student has 1 invalid answers",
            },
        ]
        temp_dir, legacy_path, new_path, result = self._write_legacy_and_new(rows)
        try:
            self.assertEqual(result.status, "ok")
            self.assertEqual(result.generated_files, ("validation_report.csv",))
            self.assertEqual(new_path.read_bytes(), legacy_path.read_bytes())
            self.assertEqual(self._read_fieldnames(new_path), VALIDATION_REPORT_FIELDNAMES)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_empty_rows_match_legacy_bytes(self):
        temp_dir, legacy_path, new_path, result = self._write_legacy_and_new([])
        try:
            self.assertEqual(result.status, "ok")
            self.assertIn("validation_report_rows_empty", result.warnings)
            self.assertEqual(new_path.read_bytes(), legacy_path.read_bytes())
            self.assertEqual(self._read_fieldnames(new_path), VALIDATION_REPORT_FIELDNAMES)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_writer_module_imports_no_legacy_or_web(self):
        source_path = PROJECT_ROOT / "app/infrastructure/exporters/validation_report_csv_exporter.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        self.assertFalse(any(name == "legacy" or name.startswith("legacy.") for name in imports))
        self.assertFalse(any(name == "web" or name.startswith("web.") for name in imports))


if __name__ == "__main__":
    unittest.main()
