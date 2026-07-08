import ast, csv, shutil, tempfile, unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class StudentReportCsvExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
    def _run(self, d): from app.workflow import run_grading; return run_grading(DEMO_KEY, DEMO_SUB, d, no_archive=True, exam_name="t")
    def _read(self, p):
        with p.open("r", encoding="utf-8-sig", newline="") as h: return list(csv.DictReader(h))

    def test_field_order(self):
        from app.infrastructure.exporters.student_report_csv_exporter import STUDENT_REPORT_FIELDNAMES
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try:
            ld = Path(t)/"l"; self._run(ld)
            with (ld/"student_report.csv").open("r", encoding="utf-8-sig", newline="") as h:
                self.assertEqual(list(STUDENT_REPORT_FIELDNAMES), csv.DictReader(h).fieldnames)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_round_trip(self):
        from app.infrastructure.exporters.student_report_csv_exporter import StudentReportCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try:
            ld = Path(t)/"l"; self._run(ld); lr = self._read(ld/"student_report.csv")
            nd = Path(t)/"n"; nd.mkdir()
            r = StudentReportCsvExporter().export(ExportRequest(output_dir=nd), lr)
            self.assertEqual(r.status, "ok")
            nr = self._read(nd/"student_report.csv")
            self.assertEqual(len(nr), len(lr)); self.assertEqual(nr[0], lr[0])
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_encoding(self):
        from app.infrastructure.exporters.student_report_csv_exporter import StudentReportCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try:
            ld = Path(t)/"l"; self._run(ld); lr = self._read(ld/"student_report.csv")
            nd = Path(t)/"n"; nd.mkdir(); StudentReportCsvExporter().export(ExportRequest(output_dir=nd), lr)
            raw = (nd/"student_report.csv").read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_empty_rows(self):
        from app.infrastructure.exporters.student_report_csv_exporter import StudentReportCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try:
            r = StudentReportCsvExporter().export(ExportRequest(output_dir=Path(t)), [])
            self.assertEqual(r.status, "ok"); self.assertIn("student_report_rows_empty", r.warnings)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/infrastructure/exporters/student_report_csv_exporter.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    self.assertFalse(getattr(n,"module","") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

    def test_old_still_passes(self):
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try: self.assertTrue(self._run(Path(t))["ok"]); self.assertTrue((Path(t)/"student_report.csv").exists())
        finally: shutil.rmtree(t, ignore_errors=True)

if __name__ == "__main__": unittest.main()
