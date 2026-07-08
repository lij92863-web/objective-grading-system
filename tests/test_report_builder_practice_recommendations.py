import ast, unittest
from pathlib import Path
from legacy.objective_grader_legacy import (build_correct_question_ids as legacy_correct_ids,
    build_target_difficulties as legacy_target_diff, recommend_practice as legacy_recommend,
    build_knowledge_profiles as legacy_build_kp, load_answer_key, load_submissions, grade_all,
    load_question_bank)
from app.application.use_cases.report_builders.practice_recommendations import (
    build_correct_question_ids, build_target_difficulties, build_practice_recommendations)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
DEMO_BANK = PROJECT_ROOT/"samples/demo_exam/question_bank_sample.csv"

class PracticeRecommendationsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
        cls._key = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, cls._key)
        cls._results = grade_all(cls._key, subs)
        cls._profiles = legacy_build_kp(cls._key, cls._results)
        cls._bank = load_question_bank(DEMO_BANK) if DEMO_BANK.exists() else None
    def _spec_to_dict(self, s):
        return dict(question=s.number, source_id=s.source_id, difficulty=s.difficulty,
                    tags=list(s.tags) if s.tags else [])
    def _result_to_dict(self, r):
        return dict(student_id=r.student_id, name=r.name,
                    details=[dict(number=d.number, status=d.status, score=d.score, max_score=d.max_score) for d in r.details])
    def _prof_to_dict(self, p):
        return dict(student_id=p.student_id, name=p.name, tag=p.tag, mastery=p.mastery, weak=p.weak)
    def _bank_to_dict(self, b):
        return dict(question_id=b.question_id, stem=b.stem, answer=b.answer, tags=list(b.tags), difficulty=b.difficulty)
    def test_correct_ids_match(self):
        specs = [self._spec_to_dict(s) for s in self._key.questions]
        results = [self._result_to_dict(r) for r in self._results]
        l = legacy_correct_ids(self._key, self._results)
        n = build_correct_question_ids(specs, results)
        self.assertEqual(set(l.keys()), set(n.keys()))
        for k in l:
            self.assertEqual(l[k], n[k], f"student {k} correct ids mismatch")
    def test_target_difficulties_match(self):
        specs = [self._spec_to_dict(s) for s in self._key.questions]
        results = [self._result_to_dict(r) for r in self._results]
        l = legacy_target_diff(self._key, self._results)
        n = build_target_difficulties(specs, results)
        self.assertEqual(set(str(k) for k in l), set(str(k) for k in n))
        for k in l:
            nk = next((nk for nk in n if str(nk) == str(k)), None)
            if nk: self.assertEqual(l[k], n[nk], f"target diff {k}")
    def test_recommend_matches(self):
        if not self._bank: self.skipTest("No question bank")
        l = legacy_recommend(self._profiles, self._bank, 3,
                             legacy_correct_ids(self._key, self._results),
                             legacy_target_diff(self._key, self._results))
        specs = [self._spec_to_dict(s) for s in self._key.questions]
        results = [self._result_to_dict(r) for r in self._results]
        profs = [self._prof_to_dict(p) for p in self._profiles]
        bank = [self._bank_to_dict(b) for b in self._bank]
        n = build_practice_recommendations(profs, bank, 3,
            build_correct_question_ids(specs, results),
            build_target_difficulties(specs, results))
        self.assertEqual(len(n), len(l))
        for i in range(len(n)):
            for k in l[i]:
                self.assertEqual(n[i].get(k), l[i].get(k), f"Row {i} {k}")
    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/application/use_cases/report_builders/practice_recommendations.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: self.assertFalse((getattr(n,"module","") or "") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

if __name__ == "__main__": unittest.main()
