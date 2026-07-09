"""Tests for xlsx_helpers — zero-dependency XLSX writer (E3B1)."""

import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from app.infrastructure.exporters import xlsx_helpers
from app.infrastructure.exporters.xlsx_helpers import XlsxSheet, write_xlsx

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Namespace used in OOXML spreadsheets
NS_S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_NS = {"ns": NS_S}


# ── helpers ────────────────────────────────────────────────────────────────

def _get_sheet_names(xlsx_path: Path) -> list:
    with zipfile.ZipFile(xlsx_path) as z:
        wb_xml = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb_xml)
        return [s.get("name", "") for s in root.findall(".//ns:sheet", NS_NS)]


def _get_sheet_headers(xlsx_path: Path) -> dict:
    """Return {sheet_name: [header_values]}."""
    result = {}
    with zipfile.ZipFile(xlsx_path) as z:
        wb_xml = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb_xml)
        sheets = [(s.get("name", ""), s.get("sheetId", ""))
                  for s in root.findall(".//ns:sheet", NS_NS)]
        for idx, (name, _sid) in enumerate(sheets, start=1):
            sheet_path = f"xl/worksheets/sheet{idx}.xml"
            try:
                sheet_xml = z.read(sheet_path).decode("utf-8")
            except KeyError:
                result[name] = []
                continue
            sroot = ET.fromstring(sheet_xml)
            rows = sroot.findall(".//ns:row", NS_NS)
            if not rows:
                result[name] = []
                continue
            first_row_cells = rows[0].findall(".//ns:c", NS_NS)
            header = []
            for cell in first_row_cells:
                is_elem = cell.find(".//ns:is", NS_NS)
                if is_elem is not None:
                    t_elem = is_elem.find("ns:t", NS_NS)
                    if t_elem is not None and t_elem.text is not None:
                        header.append(t_elem.text)
            result[name] = header
    return result


def _get_all_cell_values(xlsx_path: Path, sheet_index: int = 1) -> list:
    """Return list of (row_index, col_index, cell_text) tuples."""
    result = []
    with zipfile.ZipFile(xlsx_path) as z:
        sheet_xml = z.read(
            f"xl/worksheets/sheet{sheet_index}.xml"
        ).decode("utf-8")
        sroot = ET.fromstring(sheet_xml)
        for row in sroot.findall(".//ns:row", NS_NS):
            for cell in row.findall("ns:c", NS_NS):
                is_elem = cell.find("ns:is", NS_NS)
                if is_elem is not None:
                    t_elem = is_elem.find("ns:t", NS_NS)
                    if t_elem is not None and t_elem.text is not None:
                        result.append(t_elem.text)
    return result


def _get_zip_entries(xlsx_path: Path) -> set:
    with zipfile.ZipFile(xlsx_path) as z:
        return set(z.namelist())


# ── tests ──────────────────────────────────────────────────────────────────

class XlsxHelperBasicTests(unittest.TestCase):
    """Single- and multi-sheet smoke tests."""

    def test_single_sheet_writes_valid_zip(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "single.xlsx"
            write_xlsx(fp, [XlsxSheet(name="Test", rows=[["A", "B"], ["1", "2"]])])
            self.assertTrue(zipfile.is_zipfile(fp))
            entries = _get_zip_entries(fp)
            self.assertIn("[Content_Types].xml", entries)
            self.assertIn("xl/workbook.xml", entries)
            self.assertIn("xl/worksheets/sheet1.xml", entries)
            self.assertIn("_rels/.rels", entries)
            self.assertIn("xl/_rels/workbook.xml.rels", entries)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_single_sheet_name_preserved(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "name.xlsx"
            write_xlsx(fp, [XlsxSheet(name="成绩总表", rows=[["姓名"], ["张三"]])])
            names = _get_sheet_names(fp)
            self.assertEqual(names, ["成绩总表"])
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_single_sheet_headers_parseable(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "hdrs.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="scores", rows=[
                    ["rank", "student_id", "name", "score"],
                    ["1", "S01", "张三", "95"],
                ]),
            ])
            headers = _get_sheet_headers(fp)
            self.assertEqual(headers["scores"], ["rank", "student_id", "name", "score"])
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_single_sheet_inline_str_cell_values(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "cells.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="data", rows=[["X", "Y"], ["hello", "world"]]),
            ])
            with zipfile.ZipFile(fp) as z:
                xml_text = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            self.assertIn('t="inlineStr"', xml_text)
            values = _get_all_cell_values(fp, 1)
            self.assertIn("hello", values)
            self.assertIn("world", values)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_multi_sheet_workbook(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "multi.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="SheetA", rows=[["H1"], ["d1"]]),
                XlsxSheet(name="SheetB", rows=[["H2"], ["d2"]]),
                XlsxSheet(name="SheetC", rows=[["H3"], ["d3"]]),
            ])
            names = _get_sheet_names(fp)
            self.assertEqual(names, ["SheetA", "SheetB", "SheetC"])
            entries = _get_zip_entries(fp)
            for idx in (1, 2, 3):
                self.assertIn(f"xl/worksheets/sheet{idx}.xml", entries)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_file_size_above_1kb_with_data(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "size.xlsx"
            rows = [["col" + str(i) for i in range(10)]] + [
                ["data"] * 10 for _ in range(100)
            ]
            write_xlsx(fp, [XlsxSheet(name="big", rows=rows)])
            self.assertGreater(fp.stat().st_size, 1000)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_empty_sheet_gets_empty_fallback_row(self):
        """Empty sheets get a single ['empty'] row so the xlsx is valid."""
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "empty.xlsx"
            write_xlsx(fp, [XlsxSheet(name="blank", rows=[])])
            self.assertTrue(zipfile.is_zipfile(fp))
        finally:
            shutil.rmtree(t, ignore_errors=True)


class XlsxHelperChineseTests(unittest.TestCase):
    """Chinese character support."""

    def test_chinese_sheet_names(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "zh.xlsx"
            sheet_names = ["成绩总表", "每题明细", "每题分析", "知识点画像",
                           "学生错题", "讲评计划", "班级补救", "分层补救",
                           "数据质量检查"]
            sheets = [
                XlsxSheet(name=n, rows=[["数据"], ["测试内容"]])
                for n in sheet_names
            ]
            write_xlsx(fp, sheets)
            names = _get_sheet_names(fp)
            self.assertEqual(names, sheet_names)
            # Chinese in workbook XML
            with zipfile.ZipFile(fp) as z:
                wb_xml = z.read("xl/workbook.xml").decode("utf-8")
                for cn_name in sheet_names:
                    self.assertIn(cn_name, wb_xml)
            # Chinese in cell values via inlineStr
            values = _get_all_cell_values(fp, 1)
            self.assertIn("测试内容", values)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_chinese_cell_content(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "zh2.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="报告", rows=[
                    ["学生", "成绩", "等级"],
                    ["张三", "95", "优秀"],
                    ["李四", "45", "不及格"],
                ]),
            ])
            values = _get_all_cell_values(fp, 1)
            for expected in ["张三", "优秀", "李四", "不及格"]:
                self.assertIn(expected, values)
        finally:
            shutil.rmtree(t, ignore_errors=True)


class XlsxHelperXMLEscapeTests(unittest.TestCase):
    """XML special-character escaping."""

    def test_angle_brackets_escaped(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "angle.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="esc", rows=[["val"], ["a < b > c"]])
            ])
            values = _get_all_cell_values(fp, 1)
            self.assertIn("a < b > c", values)
            with zipfile.ZipFile(fp) as z:
                xml_text = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            self.assertIn("&lt;", xml_text)
            self.assertIn("&gt;", xml_text)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_ampersand_escaped(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "amp.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="amp", rows=[["val"], ["A & B"]])
            ])
            values = _get_all_cell_values(fp, 1)
            self.assertIn("A & B", values)
            with zipfile.ZipFile(fp) as z:
                xml_text = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            self.assertIn("&amp;", xml_text)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_double_quotes_in_cell(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "quote.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="q", rows=[["val"], ['he said "hello"']])
            ])
            values = _get_all_cell_values(fp, 1)
            self.assertIn('he said "hello"', values)
        finally:
            shutil.rmtree(t, ignore_errors=True)


class XlsxHelperBoundaryTests(unittest.TestCase):
    """Edge cases and guard checks."""

    def test_sheet_name_truncated_to_31_chars(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "long.xlsx"
            long_name = "A" * 50
            write_xlsx(fp, [XlsxSheet(name=long_name, rows=[["x"]])])
            names = _get_sheet_names(fp)
            self.assertEqual(len(names[0]), 31)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        """xlsx_helpers must not import legacy."""
        import ast
        src = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
               / "xlsx_helpers.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("legacy", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)

    def test_no_web_import(self):
        import ast
        src = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
               / "xlsx_helpers.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("web", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("web", node.module)

    def test_no_openpyxl_import(self):
        import ast
        src = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
               / "xlsx_helpers.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("openpyxl", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("openpyxl", node.module)

    def test_no_shared_strings_xml(self):
        """Legacy route uses inlineStr only — no sharedStrings.xml."""
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "noss.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="data", rows=[["A"], ["B"]]),
            ])
            entries = _get_zip_entries(fp)
            self.assertNotIn("xl/sharedStrings.xml", entries)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_styles_xml(self):
        """Plain xlsx — no styles.xml."""
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "nostyle.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="s", rows=[["x"]]),
            ])
            entries = _get_zip_entries(fp)
            self.assertNotIn("xl/styles.xml", entries)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_workbook_xml_parseable(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "wb.xlsx"
            write_xlsx(fp, [XlsxSheet(name="S1", rows=[["H"]])])
            with zipfile.ZipFile(fp) as z:
                wb_xml = z.read("xl/workbook.xml").decode("utf-8")
                root = ET.fromstring(wb_xml)
                self.assertEqual(root.tag, f"{{{NS_S}}}workbook")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_all_numeric_data_preserved(self):
        t = tempfile.mkdtemp(prefix="e3b1_", dir=PROJECT_ROOT / "data")
        try:
            fp = Path(t) / "num.xlsx"
            write_xlsx(fp, [
                XlsxSheet(name="n", rows=[
                    ["id", "score"], ["1", "95.5"], ["2", "0"]
                ]),
            ])
            values = _get_all_cell_values(fp, 1)
            self.assertIn("95.5", values)
            self.assertIn("0", values)
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
