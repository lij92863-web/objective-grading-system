import ast, unittest
from pathlib import Path
from legacy.objective_grader_legacy import build_knowledge_profiles as legacy_build_kp
from legacy.objective_grader_legacy import load_answer_key, load_submissions, grade_all
from app.application.use_cases.report_builders.knowledge_profiles import build_knowledge_profiles

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"

class KnowledgeProfilesBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo samples")
        cls._key = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, cls._key)
        cls._results = grade_all(cls._key, subs)
    def _spec_to_dict(self, s):
        return dict(question=s.number, tags=list(s.tags), points=s.points)
    def _result_to_dict(self, r):
        return dict(student_id=r.student_id, name=r.name,
                    details=[dict(number=d.number, score=d.score, max_score=d.max_score) for d in r.details])
    def test_matches_legacy(self):
        legacy_profiles = legacy_build_kp(self._key, self._results)
        specs = [self._spec_to_dict(s) for s in self._key.questions]
        results = [self._result_to_dict(r) for r in self._results]
        new_profiles = build_knowledge_profiles(specs, results)
        self.assertEqual(len(new_profiles), len(legacy_profiles))
        for i in range(len(new_profiles)):
            for k in ["student_id","tag","score","max_score","mastery","question_count"]:
                self.assertEqual(new_profiles[i].get(k), getattr(legacy_profiles[i], k, None), f"Row {i} {k}")
            # weak is boolean in legacy dataclass, "yes"/"no" in builder dict
            self.assertEqual(new_profiles[i].get("weak"), "yes" if legacy_profiles[i].weak else "no")
    def test_empty(self): self.assertEqual(build_knowledge_profiles([], []), [])
    def test_no_legacy(self):
        f = PROJECT_ROOT/"app/application/use_cases/report_builders/knowledge_profiles.py"
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names: self.assertFalse((getattr(n,"module","") or "") and (getattr(n,"module","")+"."+a.name).startswith("legacy"))

if __name__ == "__main__": unittest.main()
