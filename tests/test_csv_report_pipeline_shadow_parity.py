"""Shadow parity tests — E6B. New pipeline vs legacy CSV output."""

import csv, shutil, tempfile, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

CSV_FILES = ["summary.csv","detail.csv","item_analysis.csv","knowledge_profile.csv",
             "practice_recommendations.csv","class_report.csv","validation_report.csv","student_report.csv"]

class CsvReportPipelineShadowParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
    def _read_csv(self, p):
        with p.open("r", encoding="utf-8-sig", newline="") as h: return list(csv.DictReader(h))

    def test_8_csv_files_parity(self):
        from app.workflow import run_grading
        from app.application.use_cases.csv_report_pipeline import run_csv_report_pipeline, CsvPipelineInput
        from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all, build_knowledge_profiles

        t = tempfile.mkdtemp(prefix="s6b_", dir=PROJECT_ROOT/"data")
        try:
            # Legacy
            legacy_dir = Path(t)/"legacy"; legacy_dir.mkdir()
            run_grading(DEMO_KEY, DEMO_SUB, legacy_dir, no_archive=True, exam_name="p")

            # New pipeline
            key = load_answer_key(DEMO_KEY)
            subs = load_submissions(DEMO_SUB, key)
            results = grade_all(key, subs)
            profiles = build_knowledge_profiles(key, results)
            new_dir = Path(t)/"new"; new_dir.mkdir()
            inp = CsvPipelineInput(
                output_dir=new_dir, answer_key=key, results=results,
                submissions=subs, profiles=profiles,
                exam_meta=dict(exam_name="p", class_name="", subject="", exam_date=""),
            )
            r = run_csv_report_pipeline(inp)
            self.assertTrue(r.ok)

            for fname in CSV_FILES:
                with self.subTest(file=fname):
                    lp = legacy_dir/fname; np = new_dir/fname
                    self.assertTrue(lp.exists(), f"Legacy missing {fname}")
                    self.assertTrue(np.exists(), f"New missing {fname}")
                    lr = self._read_csv(lp); nr = self._read_csv(np)
                    self.assertEqual(len(nr), len(lr), f"{fname} row count")
                    if lr:
                        # Field order
                        with lp.open("r", encoding="utf-8-sig", newline="") as h:
                            self.assertEqual(list(csv.DictReader(h).fieldnames),
                                             list(csv.DictReader(np.open("r", encoding="utf-8-sig", newline="")).fieldnames))
                        # First row
                        self.assertEqual(nr[0], lr[0], f"{fname} first row")
                    # Encoding
                    self.assertTrue(lp.read_bytes().startswith(b"\xef\xbb\xbf") == np.read_bytes().startswith(b"\xef\xbb\xbf"))
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_pipeline_does_not_write_excel_or_html(self):
        from app.application.use_cases.csv_report_pipeline import run_csv_report_pipeline, CsvPipelineInput
        from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all, build_knowledge_profiles
        t = tempfile.mkdtemp(prefix="s6b_", dir=PROJECT_ROOT/"data")
        try:
            key = load_answer_key(DEMO_KEY); subs = load_submissions(DEMO_SUB, key)
            results = grade_all(key, subs); profiles = build_knowledge_profiles(key, results)
            new_dir = Path(t)/"new"; new_dir.mkdir()
            run_csv_report_pipeline(CsvPipelineInput(
                output_dir=new_dir, answer_key=key, results=results,
                submissions=subs, profiles=profiles,
                exam_meta=dict(exam_name="p", class_name="", subject="", exam_date="")))
            self.assertFalse((new_dir/"exam_report.xlsx").exists())
            self.assertFalse((new_dir/"index.html").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

if __name__ == "__main__": unittest.main()
