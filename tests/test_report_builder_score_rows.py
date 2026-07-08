import ast, unittest
from pathlib import Path
from legacy.objective_grader_legacy import simple_score_rows as legacy_simple_score_rows
from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all
from app.application.use_cases.report_builders.score_rows import build_simple_score_rows

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class ScoreRowsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
        key = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, key)
        cls._results = grade_all(key, subs)
    def _to_dict(self, r):
        return dict(student_id=r.student_id, name=r.name, score=r.score, max_score=r.max_score,
                    percent=r.percent, correct_count=r.correct_count,
                    wrong_or_partial_count=r.wrong_or_partial_count, blank_count=r.blank_count,
                    invalid_count=r.invalid_count,
                    details=[dict(number=d.number, status=d.status, score=d.score, max_score=d.max_score) for d in r.details])
    def test_matches_legacy(self):
        legacy_rows = legacy_simple_score_rows(self._results)
        new_rows = build_simple_score_rows([self._to_dict(r) for r in self._results])
        self.assertEqual(len(new_rows), len(legacy_rows))
        for i in range(len(new_rows)):
            for k in legacy_rows[i]:
                self.assertEqual(new_rows[i].get(k), legacy_rows[i].get(k), f"Row {i} key {k} mismatch")
    def test_field_order(self):
        rows = build_simple_score_rows([self._to_dict(r) for r in self._results])
        self.assertGreater(len(rows), 0)
        self.assertIn("rank", rows[0]); self.assertIn("student_id", rows[0])
    def test_empty_input(self):
        self.assertEqual(build_simple_score_rows([]), [])
    def test_no_legacy_import(self):
        f = PROJECT_ROOT/"app/application/use_cases/report_builders/score_rows.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: self.assertFalse((getattr(n,"module","") or "") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

if __name__ == "__main__": unittest.main()
