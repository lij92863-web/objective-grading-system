import ast, csv, shutil, tempfile, unittest
from pathlib import Path
from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all
from app.application.use_cases.report_builders.item_analysis import build_item_analysis_rows

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class ItemAnalysisBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
        cls._key = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, cls._key)
        cls._results = grade_all(cls._key, subs)

    def _read_csv(self, p):
        with p.open("r", encoding="utf-8-sig", newline="") as h: return list(csv.DictReader(h))

    def test_matches_legacy(self):
        # Run legacy workflow to get item_analysis.csv, compare with builder output
        from app.workflow import run_grading
        t = tempfile.mkdtemp(prefix="ia_", dir=PROJECT_ROOT/"data")
        try:
            run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="t")
            legacy_rows = self._read_csv(Path(t)/"item_analysis.csv")

            specs = [dict(question=s.number, source_id=s.source_id, status=s.status,
                          difficulty=s.difficulty, tags=list(s.tags),
                          answer_text=getattr(s,'answer_text','') or ''.join(sorted(s.answers)),
                          answer=''.join(sorted(s.answers)), points=s.points)
                     for s in self._key.questions]
            results_d = [dict(student_id=r.student_id,
                              details=[dict(number=d.number, status=d.status,
                                            actual=''.join(sorted(d.actual)),
                                            normalized_answer=''.join(sorted(d.actual)))
                                       for d in r.details]) for r in self._results]
            new_rows = build_item_analysis_rows(specs, results_d)
            self.assertEqual(len(new_rows), len(legacy_rows))
            for i in range(len(new_rows)):
                for k in legacy_rows[i]:
                    self.assertEqual(str(new_rows[i].get(k)), str(legacy_rows[i].get(k)),
                                     f"Row {i} key {k}")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_empty(self): self.assertEqual(build_item_analysis_rows([], []), [])

    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/application/use_cases/report_builders/item_analysis.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: self.assertFalse((getattr(n,"module","") or "") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

if __name__ == "__main__": unittest.main()
