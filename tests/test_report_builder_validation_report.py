import ast, unittest
from pathlib import Path
from legacy.objective_grader_legacy import build_validation_report as legacy_build_vr
from legacy.objective_grader_legacy import build_knowledge_profiles as legacy_build_kp
from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all
from app.application.use_cases.report_builders.validation_report import build_validation_report

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class ValidationReportBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
        cls._key = load_answer_key(DEMO_KEY)
        cls._subs = load_submissions(DEMO_SUB, cls._key)
        cls._results = grade_all(cls._key, cls._subs)
        cls._profiles = legacy_build_kp(cls._key, cls._results)
    def _ak_to_dict(self):
        by_number = {s.number: dict(question=s.number, source_id=s.source_id, tags=list(s.tags), status=s.status, points=s.points) for s in self._key.questions}
        questions = [dict(question=s.number, source_id=s.source_id, tags=list(s.tags), status=s.status, points=s.points) for s in self._key.questions]
        return dict(by_number=by_number, questions=questions, duplicate_questions=list(self._key.duplicate_questions) if hasattr(self._key, 'duplicate_questions') else [])
    def _sub_to_dict(self, s):
        return dict(student_id=s.student_id, name=s.name,
                    answers={k: frozenset(v) for k,v in s.answers.items()},
                    raw_answers=dict(s.raw_answers), extra_questions=list(s.extra_questions))
    def _prof_to_dict(self, p):
        return dict(student_id=p.student_id, tag=p.tag, weak=p.weak)
    def _result_to_dict(self, r):
        return dict(student_id=r.student_id, name=r.name, details=[])
    def test_matches_legacy(self):
        legacy_rows = legacy_build_vr(self._key, self._subs, self._results, self._profiles, None)
        ak = self._ak_to_dict()
        subs = [self._sub_to_dict(s) for s in self._subs]
        profs = [self._prof_to_dict(p) for p in self._profiles]
        results = [self._result_to_dict(r) for r in self._results]
        new_rows = build_validation_report(ak, subs, results, profs, None)
        self.assertEqual(len(new_rows), len(legacy_rows))
        for i in range(len(new_rows)):
            for k in legacy_rows[i]:
                self.assertEqual(new_rows[i].get(k), legacy_rows[i].get(k), f"Row {i} {k}")
    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/application/use_cases/report_builders/validation_report.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: self.assertFalse((getattr(n,"module","") or "") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

if __name__ == "__main__": unittest.main()
