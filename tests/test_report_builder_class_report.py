import ast, unittest
from pathlib import Path
from legacy.objective_grader_legacy import build_class_report as legacy_build_cr, ExamMeta
from legacy.objective_grader_legacy import build_knowledge_profiles as legacy_build_kp
from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all
from app.application.use_cases.report_builders.class_report import build_class_report

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class ClassReportBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
        cls._key = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, cls._key)
        cls._results = grade_all(cls._key, subs)
        cls._profiles = legacy_build_kp(cls._key, cls._results)
    def _spec_to_dict(self, s):
        return dict(question=s.number, tags=list(s.tags), points=s.points, status=s.status)
    def _result_to_dict(self, r):
        return dict(student_id=r.student_id, name=r.name, score=r.score, max_score=r.max_score,
                    percent=r.percent,
                    details=[dict(number=d.number, status=d.status, score=d.score, max_score=d.max_score,
                                  actual="".join(sorted(d.actual)), normalized_answer="".join(sorted(d.actual))) for d in r.details])
    def _profile_to_dict(self, p):
        return dict(student_id=p.student_id, name=p.name, tag=p.tag, score=p.score, max_score=p.max_score,
                    mastery=p.mastery, question_count=p.question_count, weak=p.weak)
    def test_matches_legacy(self):
        meta = ExamMeta(exam_name="test", class_name="Test", subject="Math", exam_date="2025-01-01")
        legacy_rows = legacy_build_cr(self._key, self._results, self._profiles, meta)
        specs = [self._spec_to_dict(s) for s in self._key.questions]
        results = [self._result_to_dict(r) for r in self._results]
        profiles = [self._profile_to_dict(p) for p in self._profiles]
        meta_dict = dict(exam_name="test", class_name="Test", subject="Math", exam_date="2025-01-01")
        new_rows = build_class_report(meta_dict, specs, results, profiles)
        self.assertEqual(len(new_rows), len(legacy_rows))
        for i in range(len(new_rows)):
            for k in legacy_rows[i]:
                self.assertEqual(new_rows[i].get(k), legacy_rows[i].get(k), f"Row {i} {k}")
    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/application/use_cases/report_builders/class_report.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: self.assertFalse((getattr(n,"module","") or "") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

if __name__ == "__main__": unittest.main()
