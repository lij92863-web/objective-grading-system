"""Tests for WorkbookExporter — E3C."""

import ast
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.workbook_exporter import (
    EXPECTED_SHEETS,
    OUTPUT_FILENAME,
    WorkbookExporter,
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


def _get_sheet_row_counts(xlsx_path: Path) -> dict:
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
    """Return {sheet_name: [cell_values]} for row 2."""
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


class WorkbookExporterTests(unittest.TestCase):
    """Full workbook comparison against legacy output."""

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _run_legacy_and_get_csvs(self):
        """Run legacy workflow, return (legacy_xlsx, list of (name, csv_path), tmpdir)."""
        t = tempfile.mkdtemp(prefix="e3c_leg_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                        no_archive=True, exam_name="x")
            legacy_xlsx = Path(t) / "exam_report.xlsx"
            # Build the csv_path list matching the workflow report_files
            csv_name_to_path = {
                "summary.csv": "summary.csv",
                "detail.csv": "detail.csv",
                "item_analysis.csv": "item_analysis.csv",
                "knowledge_profile.csv": "knowledge_profile.csv",
                "student_wrong_list.csv": "student_wrong_list.csv",
                "teaching_plan.csv": "teaching_plan.csv",
                "class_remedial_package.csv": "class_remedial_package.csv",
                "layered_remedial_plan.csv": "layered_remedial_plan.csv",
                "validation_report.csv": "validation_report.csv",
            }
            report_files = [
                (sheet_name, Path(t) / csv_filename)
                for (sheet_name, csv_filename) in EXPECTED_SHEETS
            ]
            return legacy_xlsx, report_files, t
        except Exception:
            shutil.rmtree(t, ignore_errors=True)
            raise

    def test_exporter_writes_valid_xlsx(self):
        legacy_xlsx, report_files, t = self._run_legacy_and_get_csvs()
        try:
            # Write new exporter output to a subdir so names don't clash
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            result = WorkbookExporter().export(req, report_files)
            self.assertEqual(result.status, "ok")
            new_xlsx = Path(result.generated_files[0])
            self.assertTrue(new_xlsx.exists())
            self.assertTrue(zipfile.is_zipfile(new_xlsx))
            self.assertGreater(new_xlsx.stat().st_size, 1000)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_sheet_names_and_order_match_legacy(self):
        legacy_xlsx, report_files, t = self._run_legacy_and_get_csvs()
        try:
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            result = WorkbookExporter().export(req, report_files)
            new_xlsx = Path(result.generated_files[0])
            legacy_names = _get_sheet_names(legacy_xlsx)
            new_names = _get_sheet_names(new_xlsx)
            expected_names = [name for name, _ in EXPECTED_SHEETS]
            self.assertEqual(legacy_names, expected_names)
            self.assertEqual(new_names, expected_names)
            self.assertEqual(legacy_names, new_names,
                             f"Sheet order/name mismatch:\nlegacy={legacy_names}\nnew={new_names}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_sheet_count_matches_legacy(self):
        legacy_xlsx, report_files, t = self._run_legacy_and_get_csvs()
        try:
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            result = WorkbookExporter().export(req, report_files)
            new_xlsx = Path(result.generated_files[0])
            legacy_names = _get_sheet_names(legacy_xlsx)
            new_names = _get_sheet_names(new_xlsx)
            self.assertEqual(len(legacy_names), 9)
            self.assertEqual(len(legacy_names), len(new_names))
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_headers_match_legacy_for_key_sheets(self):
        legacy_xlsx, report_files, t = self._run_legacy_and_get_csvs()
        try:
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            result = WorkbookExporter().export(req, report_files)
            new_xlsx = Path(result.generated_files[0])
            leg_h = _get_sheet_headers(legacy_xlsx)
            new_h = _get_sheet_headers(new_xlsx)
            key_sheets = ["成绩总表", "每题明细", "每题分析"]
            for name in key_sheets:
                self.assertIn(name, leg_h, f"Missing legacy sheet: {name}")
                self.assertIn(name, new_h, f"Missing new sheet: {name}")
                self.assertEqual(leg_h[name], new_h[name],
                                 f"Header mismatch for '{name}'")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_first_data_rows_match_for_key_sheets(self):
        legacy_xlsx, report_files, t = self._run_legacy_and_get_csvs()
        try:
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            result = WorkbookExporter().export(req, report_files)
            new_xlsx = Path(result.generated_files[0])
            leg_first = _get_first_data_row(legacy_xlsx)
            new_first = _get_first_data_row(new_xlsx)
            for name in ["成绩总表", "每题明细", "每题分析"]:
                self.assertEqual(
                    leg_first.get(name, []), new_first.get(name, []),
                    f"First row mismatch for '{name}'")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_chinese_not_garbled(self):
        legacy_xlsx, report_files, t = self._run_legacy_and_get_csvs()
        try:
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)
            result = WorkbookExporter().export(req, report_files)
            new_xlsx = Path(result.generated_files[0])
            with zipfile.ZipFile(new_xlsx) as z:
                wb = z.read("xl/workbook.xml").decode("utf-8")
                for cn_name, _ in EXPECTED_SHEETS:
                    self.assertIn(cn_name, wb,
                                  f"Chinese sheet name '{cn_name}' missing")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src_path = (
            PROJECT_ROOT / "app" / "infrastructure" / "exporters"
            / "workbook_exporter.py"
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
            / "workbook_exporter.py"
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
            / "workbook_exporter.py"
        )
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("openpyxl", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("openpyxl", node.module)

    def test_old_workflow_still_unaffected(self):
        """Running the real workflow still produces the legacy xlsx."""
        t = tempfile.mkdtemp(prefix="e3c_wf_", dir=PROJECT_ROOT / "data")
        try:
            from app.workflow import run_grading
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t),
                            no_archive=True, exam_name="x")
            self.assertTrue(r["ok"])
            self.assertTrue((Path(t) / "exam_report.xlsx").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
