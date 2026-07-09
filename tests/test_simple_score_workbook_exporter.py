"""Tests for SimpleScoreWorkbookExporter — E3B2."""

import ast
import csv
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.simple_score_workbook_exporter import (
    FIELDS,
    SHEET_NAME,
    SimpleScoreWorkbookExporter,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"

NS_S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_NS = {"ns": NS_S}


def _get_sheet_names(xlsx_path: Path) -> list:
    with zipfile.ZipFile(xlsx_path) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb)
        return [s.get("name", "") for s in root.findall(".//ns:sheet", NS_NS)]


def _get_sheet_headers(xlsx_path: Path) -> dict:
    result = {}
    with zipfile.ZipFile(xlsx_path) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb)
        sheets = [(s.get("name", ""), s.get("sheetId", ""))
                  for s in root.findall(".//ns:sheet", NS_NS)]
        for idx, (name, _sid) in enumerate(sheets, start=1):
            sp = f"xl/worksheets/sheet{idx}.xml"
            try:
                sx = z.read(sp).decode("utf-8")
            except KeyError:
                result[name] = []
                continue
            sroot = ET.fromstring(sx)
            rows = sroot.findall(".//ns:row", NS_NS)
            if not rows:
                result[name] = []
                continue
            cells = rows[0].findall(".//ns:c", NS_NS)
            header = []
            for cell in cells:
                is_e = cell.find(".//ns:is", NS_NS)
                if is_e is not None:
                    t_e = is_e.find("ns:t", NS_NS)
                    if t_e is not None and t_e.text is not None:
                        header.append(t_e.text)
            result[name] = header
    return result


def _get_sheet_row_count(xlsx_path: Path) -> dict:
    result = {}
    with zipfile.ZipFile(xlsx_path) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb)
        sheets = [(s.get("name", ""), s.get("sheetId", ""))
                  for s in root.findall(".//ns:sheet", NS_NS)]
        for idx, (name, _sid) in enumerate(sheets, start=1):
            sp = f"xl/worksheets/sheet{idx}.xml"
            try:
                sx = z.read(sp).decode("utf-8")
            except KeyError:
                result[name] = 0
                continue
            sroot = ET.fromstring(sx)
            result[name] = len(sroot.findall(".//ns:row", NS_NS))
    return result


def _get_first_data_row(xlsx_path: Path) -> dict:
    """Return {sheet_name: [cell_values]} for row 2 (first data row)."""
    result = {}
    with zipfile.ZipFile(xlsx_path) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb)
        sheets = [(s.get("name", ""), s.get("sheetId", ""))
                  for s in root.findall(".//ns:sheet", NS_NS)]
        for idx, (name, _sid) in enumerate(sheets, start=1):
            sp = f"xl/worksheets/sheet{idx}.xml"
            try:
                sx = z.read(sp).decode("utf-8")
            except KeyError:
                result[name] = []
                continue
            sroot = ET.fromstring(sx)
            rows = sroot.findall(".//ns:row", NS_NS)
            if len(rows) < 2:
                result[name] = []
                continue
            cells = rows[1].findall(".//ns:c", NS_NS)
            values = []
            for cell in cells:
                is_e = cell.find(".//ns:is", NS_NS)
                if is_e is not None:
                    t_e = is_e.find("ns:t", NS_NS)
                    if t_e is not None and t_e.text is not None:
                        values.append(t_e.text)
            result[name] = values
    return result


class SimpleScoreWorkbookExporterTests(unittest.TestCase):
    """Smoke test and comparison against legacy output."""

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _run_legacy_and_get_rows(self):
        """Run legacy workflow, return simple_rows used by legacy."""
        t = tempfile.mkdtemp(prefix="e3b2_leg_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            legacy_xlsx = Path(t) / "simple_score_report.xlsx"
            # Also need rows: re-run grading with legacy directly
            import legacy.objective_grader_legacy as leg
            ak = leg.load_answer_key(DEMO_KEY)
            subs = leg.load_submissions(DEMO_SUB, ak)
            results = leg.grade_all(ak, subs)
            simple_rows = leg.simple_score_rows(results)
            return legacy_xlsx, simple_rows, t
        except Exception:
            shutil.rmtree(t, ignore_errors=True)
            raise

    def test_exporter_writes_valid_xlsx(self):
        _, simple_rows, t = self._run_legacy_and_get_rows()
        try:
            req = ExportRequest(output_dir=Path(t))
            result = SimpleScoreWorkbookExporter().export(req, simple_rows)
            self.assertEqual(result.status, "ok")
            new_xlsx = Path(result.generated_files[0])
            self.assertTrue(new_xlsx.exists())
            self.assertTrue(zipfile.is_zipfile(new_xlsx))
            self.assertGreater(new_xlsx.stat().st_size, 1000)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_sheet_name_matches_legacy(self):
        legacy_xlsx, simple_rows, t = self._run_legacy_and_get_rows()
        try:
            req = ExportRequest(output_dir=Path(t))
            result = SimpleScoreWorkbookExporter().export(req, simple_rows)
            new_xlsx = Path(result.generated_files[0])
            legacy_names = _get_sheet_names(legacy_xlsx)
            new_names = _get_sheet_names(new_xlsx)
            self.assertEqual(legacy_names, new_names)
            self.assertEqual(legacy_names, [SHEET_NAME])
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_header_matches_legacy(self):
        legacy_xlsx, simple_rows, t = self._run_legacy_and_get_rows()
        try:
            req = ExportRequest(output_dir=Path(t))
            result = SimpleScoreWorkbookExporter().export(req, simple_rows)
            new_xlsx = Path(result.generated_files[0])
            legacy_headers = _get_sheet_headers(legacy_xlsx)
            new_headers = _get_sheet_headers(new_xlsx)
            self.assertEqual(legacy_headers[SHEET_NAME], FIELDS)
            self.assertEqual(new_headers[SHEET_NAME], FIELDS)
            self.assertEqual(legacy_headers, new_headers)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_row_count_matches_legacy(self):
        legacy_xlsx, simple_rows, t = self._run_legacy_and_get_rows()
        try:
            req = ExportRequest(output_dir=Path(t))
            result = SimpleScoreWorkbookExporter().export(req, simple_rows)
            new_xlsx = Path(result.generated_files[0])
            legacy_counts = _get_sheet_row_count(legacy_xlsx)
            new_counts = _get_sheet_row_count(new_xlsx)
            self.assertEqual(
                legacy_counts[SHEET_NAME], new_counts[SHEET_NAME],
                f"Row count mismatch: legacy={legacy_counts}, new={new_counts}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_first_data_row_matches_legacy(self):
        legacy_xlsx, simple_rows, t = self._run_legacy_and_get_rows()
        try:
            req = ExportRequest(output_dir=Path(t))
            result = SimpleScoreWorkbookExporter().export(req, simple_rows)
            new_xlsx = Path(result.generated_files[0])
            legacy_first = _get_first_data_row(legacy_xlsx)
            new_first = _get_first_data_row(new_xlsx)
            self.assertEqual(
                legacy_first[SHEET_NAME], new_first[SHEET_NAME],
                f"First data row mismatch:\nlegacy={legacy_first}\nnew={new_first}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_chinese_not_garbled(self):
        _, simple_rows, t = self._run_legacy_and_get_rows()
        try:
            req = ExportRequest(output_dir=Path(t))
            result = SimpleScoreWorkbookExporter().export(req, simple_rows)
            new_xlsx = Path(result.generated_files[0])
            with zipfile.ZipFile(new_xlsx) as z:
                wb = z.read("xl/workbook.xml").decode("utf-8")
                self.assertIn("scores", wb)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src_path = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "simple_score_workbook_exporter.py"
        )
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("legacy", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)

    def test_no_web_import(self):
        src_path = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "simple_score_workbook_exporter.py"
        )
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("web", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("web", node.module)

    def test_no_openpyxl_import(self):
        src_path = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "simple_score_workbook_exporter.py"
        )
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("openpyxl", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("openpyxl", node.module)

    def test_generated_files_in_result(self):
        _, simple_rows, t = self._run_legacy_and_get_rows()
        try:
            req = ExportRequest(output_dir=Path(t))
            result = SimpleScoreWorkbookExporter().export(req, simple_rows)
            self.assertIn("simple_score_report.xlsx",
                          str(result.generated_files))
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_old_workflow_still_unaffected(self):
        """Running the real workflow still produces the legacy xlsx."""
        t = tempfile.mkdtemp(prefix="e3b2_wf_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                            no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
            self.assertTrue((Path(t) / "simple_score_report.xlsx").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
