"""Excel shadow parity tests — E3D.

Proves legacy Excel output == new exporter output at the structural level.
Does NOT require binary-identical files (timestamps may differ).
"""

import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.simple_score_workbook_exporter import (
    SimpleScoreWorkbookExporter,
)
from app.infrastructure.exporters.workbook_exporter import (
    EXPECTED_SHEETS,
    WorkbookExporter,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"

NS_S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_NS = {"ns": NS_S}


# ── parsing helpers (stdlib only) ─────────────────────────────────────────

def _sheet_names(xlsx: Path) -> list:
    with zipfile.ZipFile(xlsx) as z:
        wb = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb)
        return [s.get("name", "") for s in root.findall(".//ns:sheet", NS_NS)]


def _sheet_headers(xlsx: Path) -> dict:
    result = {}
    with zipfile.ZipFile(xlsx) as z:
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
            hdr = []
            for cell in cells:
                is_e = cell.find(".//ns:is", NS_NS)
                if is_e is not None:
                    t_e = is_e.find("ns:t", NS_NS)
                    if t_e is not None and t_e.text is not None:
                        hdr.append(t_e.text)
            result[name] = hdr
    return result


def _sheet_row_counts(xlsx: Path) -> dict:
    result = {}
    with zipfile.ZipFile(xlsx) as z:
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


def _sheet_row_values(xlsx: Path, row_num: int) -> dict:
    """Return {sheet_name: [cell_values]} for a specific row (1-based)."""
    result = {}
    with zipfile.ZipFile(xlsx) as z:
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
            if len(rows) < row_num:
                result[name] = []
                continue
            cells = rows[row_num - 1].findall(".//ns:c", NS_NS)
            values = []
            for cell in cells:
                is_e = cell.find(".//ns:is", NS_NS)
                if is_e is not None:
                    t_e = is_e.find("ns:t", NS_NS)
                    if t_e is not None and t_e.text is not None:
                        values.append(t_e.text)
            result[name] = values
    return result


class ExcelShadowParityTests(unittest.TestCase):
    """Structural parity between legacy and new Excel exporters."""

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def _generate_both(self):
        """Produce legacy and new outputs from the same grading inputs."""
        t = tempfile.mkdtemp(prefix="e3d_", dir=PROJECT_ROOT / "data")
        try:
            # 1. Legacy workflow
            import legacy.objective_grader_legacy as leg
            ak = leg.load_answer_key(DEMO_KEY)
            subs = leg.load_submissions(DEMO_SUB, ak)
            results = leg.grade_all(ak, subs)

            legacy_dir = Path(t) / "legacy"
            legacy_dir.mkdir()
            # Legacy simple score workbook
            simple_rows = leg.simple_score_rows(results)
            leg.write_simple_score_workbook(
                legacy_dir / "simple_score_report.xlsx", simple_rows)
            # Legacy workbook needs CSVs first
            from app.workflow import run_grading
            run_grading(DEMO_KEY, DEMO_SUB, legacy_dir,
                        no_archive=True, exam_name="x")

            # 2. New exporter
            new_dir = Path(t) / "new"
            new_dir.mkdir()
            req = ExportRequest(output_dir=new_dir)

            # Simple score
            SimpleScoreWorkbookExporter().export(req, simple_rows)

            # Full workbook — build same csv_path list as workflow
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
                (sheet_name, legacy_dir / csv_filename)
                for (sheet_name, csv_filename) in EXPECTED_SHEETS
            ]
            WorkbookExporter().export(req, report_files)

            return legacy_dir, new_dir, t
        except Exception:
            shutil.rmtree(t, ignore_errors=True)
            raise

    # ── simple score workbook parity ──────────────────────────────────────

    def test_simple_score_file_exists(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg = leg_dir / "simple_score_report.xlsx"
            new = new_dir / "simple_score_report.xlsx"
            self.assertTrue(leg.exists())
            self.assertTrue(new.exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_score_zip_valid(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            for fp in [leg_dir / "simple_score_report.xlsx",
                        new_dir / "simple_score_report.xlsx"]:
                self.assertTrue(zipfile.is_zipfile(fp))
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_score_sheet_names_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_n = _sheet_names(leg_dir / "simple_score_report.xlsx")
            new_n = _sheet_names(new_dir / "simple_score_report.xlsx")
            self.assertEqual(leg_n, new_n)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_score_headers_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_h = _sheet_headers(leg_dir / "simple_score_report.xlsx")
            new_h = _sheet_headers(new_dir / "simple_score_report.xlsx")
            self.assertEqual(leg_h, new_h)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_score_row_counts_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_c = _sheet_row_counts(leg_dir / "simple_score_report.xlsx")
            new_c = _sheet_row_counts(new_dir / "simple_score_report.xlsx")
            self.assertEqual(leg_c, new_c)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_score_first_row_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_r = _sheet_row_values(
                leg_dir / "simple_score_report.xlsx", 2)
            new_r = _sheet_row_values(
                new_dir / "simple_score_report.xlsx", 2)
            self.assertEqual(leg_r, new_r)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_simple_score_file_size_above_1kb(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            for fp in [leg_dir / "simple_score_report.xlsx",
                        new_dir / "simple_score_report.xlsx"]:
                self.assertGreater(fp.stat().st_size, 1000)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    # ── full workbook parity ──────────────────────────────────────────────

    def test_full_workbook_file_exists(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            self.assertTrue((leg_dir / "exam_report.xlsx").exists())
            self.assertTrue((new_dir / "exam_report.xlsx").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_full_workbook_zip_valid(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            for fp in [leg_dir / "exam_report.xlsx",
                        new_dir / "exam_report.xlsx"]:
                self.assertTrue(zipfile.is_zipfile(fp))
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_full_workbook_sheet_names_and_order_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_n = _sheet_names(leg_dir / "exam_report.xlsx")
            new_n = _sheet_names(new_dir / "exam_report.xlsx")
            self.assertEqual(leg_n, new_n,
                             f"Sheet order/name mismatch:\nlegacy={leg_n}\nnew={new_n}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_full_workbook_sheet_count_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_n = _sheet_names(leg_dir / "exam_report.xlsx")
            new_n = _sheet_names(new_dir / "exam_report.xlsx")
            self.assertEqual(len(leg_n), 9)
            self.assertEqual(len(leg_n), len(new_n))
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_full_workbook_headers_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_h = _sheet_headers(leg_dir / "exam_report.xlsx")
            new_h = _sheet_headers(new_dir / "exam_report.xlsx")
            # Compare all sheets
            for name in leg_h:
                self.assertIn(name, new_h,
                              f"Sheet '{name}' missing from new exporter")
                self.assertEqual(leg_h[name], new_h[name],
                                 f"Header mismatch for '{name}':\n"
                                 f"legacy={leg_h[name]}\nnew={new_h[name]}")
            # Also verify no extra sheets in new
            for name in new_h:
                self.assertIn(name, leg_h,
                              f"Extra sheet '{name}' in new exporter")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_full_workbook_key_sheet_first_rows_equal(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            leg_r = _sheet_row_values(leg_dir / "exam_report.xlsx", 2)
            new_r = _sheet_row_values(new_dir / "exam_report.xlsx", 2)
            for name in ["成绩总表", "每题明细", "每题分析"]:
                self.assertEqual(
                    leg_r.get(name, []), new_r.get(name, []),
                    f"First data row mismatch for '{name}'")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_full_workbook_chinese_preserved(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            for fp in [leg_dir / "exam_report.xlsx",
                        new_dir / "exam_report.xlsx"]:
                with zipfile.ZipFile(fp) as z:
                    wb = z.read("xl/workbook.xml").decode("utf-8")
                    for cn_name, _ in EXPECTED_SHEETS:
                        self.assertIn(cn_name, wb)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_full_workbook_file_size_above_1kb(self):
        leg_dir, new_dir, t = self._generate_both()
        try:
            for fp in [leg_dir / "exam_report.xlsx",
                        new_dir / "exam_report.xlsx"]:
                self.assertGreater(fp.stat().st_size, 1000)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    # ── safety ────────────────────────────────────────────────────────────

    def test_old_cli_still_works(self):
        """Smoke: the old CLI entrypoint still runs."""
        import subprocess
        import sys
        t = tempfile.mkdtemp(prefix="e3d_cli_", dir=PROJECT_ROOT / "data")
        try:
            r = subprocess.run([
                sys.executable,
                str(PROJECT_ROOT / "objective_grader.py"),
                "--answer-key", str(DEMO_KEY),
                "--submissions", str(DEMO_SUB),
                "--out-dir", str(Path(t) / "out"),
                "--no-archive",
            ], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0,
                             f"CLI failed:\n{r.stderr}")
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
