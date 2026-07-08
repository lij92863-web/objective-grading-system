import ast, unittest
from pathlib import Path
from legacy.objective_grader_legacy import item_stats as legacy_item_stats
from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all, format_expected_answer
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
    def _spec_to_dict(self, s):
        return dict(question=s.number, tags=list(s.tags), answer=s.answer_text or "".join(sorted(s.answers)),
                    points=s.points, source_id=s.source_id, status=s.status, difficulty=s.difficulty)
    def _result_to_dict(self, r):
        return dict(student_id=r.student_id, name=r.name,
                    details=[dict(number=d.number, status=d.status, actual="".join(sorted(d.actual)),
                                  normalized_answer="".join(sorted(d.actual)), score=d.score, max_score=d.max_score) for d in r.details])
    def test_matches_legacy(self):
        legacy_rows = legacy_item_stats(self._key, self._results)
        specs = [self._spec_to_dict(s) for s in self._key.questions]
        results = [self._result_to_dict(r) for r in self._results]
        new_rows = build_item_analysis_rows(specs, results)
        self.assertEqual(len(new_rows), len(legacy_rows))
        for i in range(len(new_rows)):
            # Compare all keys present in legacy row
            for k in legacy_rows[i]:
                self.assertEqual(new_rows[i].get(k), legacy_rows[i].get(k),
                                 f"Row {i} key {k}")
    def test_empty(self): self.assertEqual(build_item_analysis_rows([], []), [])
    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/application/use_cases/report_builders/item_analysis.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: self.assertFalse((getattr(n,"module","") or "") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

if __name__ == "__main__": unittest.main()
