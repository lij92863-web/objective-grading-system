import ast, csv, shutil, tempfile, unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class PracticeRecommendationsCsvExporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
    def _run(self, d): from app.workflow import run_grading; return run_grading(DEMO_KEY, DEMO_SUB, d, no_archive=True, exam_name="t")
    def _read(self, p):
        with p.open("r", encoding="utf-8-sig", newline="") as h: return list(csv.DictReader(h))

    def test_field_order(self):
        from app.infrastructure.exporters.practice_recommendations_csv_exporter import PRACTICE_RECOMMENDATIONS_FIELDNAMES
        self.assertEqual(len(PRACTICE_RECOMMENDATIONS_FIELDNAMES), 11)
        self.assertIn("student_id", PRACTICE_RECOMMENDATIONS_FIELDNAMES)

    def test_round_trip_synthetic(self):
        from app.infrastructure.exporters.practice_recommendations_csv_exporter import PracticeRecommendationsCsvExporter, PRACTICE_RECOMMENDATIONS_FIELDNAMES
        from app.infrastructure.exporters.contracts import ExportRequest
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try:
            rows = [{f: "x" for f in PRACTICE_RECOMMENDATIONS_FIELDNAMES}]
            nd = Path(t)/"n"; nd.mkdir()
            r = PracticeRecommendationsCsvExporter().export(ExportRequest(output_dir=nd), rows)
            self.assertEqual(r.status, "ok")
            nr = self._read(nd/"practice_recommendations.csv")
            self.assertEqual(len(nr), 1)
            self.assertEqual(nr[0]["student_id"], "x")
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_encoding(self):
        from app.infrastructure.exporters.practice_recommendations_csv_exporter import PracticeRecommendationsCsvExporter, PRACTICE_RECOMMENDATIONS_FIELDNAMES
        from app.infrastructure.exporters.contracts import ExportRequest
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try:
            nd = Path(t)/"n"; nd.mkdir()
            PracticeRecommendationsCsvExporter().export(ExportRequest(output_dir=nd),
                [{f: "v" for f in PRACTICE_RECOMMENDATIONS_FIELDNAMES}])
            raw = (nd/"practice_recommendations.csv").read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_empty_rows(self):
        from app.infrastructure.exporters.practice_recommendations_csv_exporter import PracticeRecommendationsCsvExporter
        from app.infrastructure.exporters.contracts import ExportRequest
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try:
            r = PracticeRecommendationsCsvExporter().export(ExportRequest(output_dir=Path(t)), [])
            self.assertEqual(r.status, "ok")
            self.assertIn("practice_recommendations_rows_empty", r.warnings)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/infrastructure/exporters/practice_recommendations_csv_exporter.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    self.assertFalse(getattr(n,"module","") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

    def test_old_still_passes(self):
        t = tempfile.mkdtemp(prefix="t_", dir=PROJECT_ROOT/"data")
        try: self.assertTrue(self._run(Path(t))["ok"])
        finally: shutil.rmtree(t, ignore_errors=True)

if __name__ == "__main__": unittest.main()
