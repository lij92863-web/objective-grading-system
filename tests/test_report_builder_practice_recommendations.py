"""Practice recommendations builder — fixture baseline (B4)."""
import json, ast, unittest
from pathlib import Path
from app.application.use_cases.report_builders.practice_recommendations import (
    build_correct_question_ids, build_target_difficulties, build_practice_recommendations,
)
from app.application.use_cases.csv_report_pipeline import _legacy_result_to_dict, _legacy_spec_to_dict

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"
DEMO_KEY = Path(__file__).parents[1] / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = Path(__file__).parents[1] / "samples/demo_exam/submissions_sample.csv"
DEMO_BANK = Path(__file__).parents[1] / "samples/demo_exam/question_bank_sample.csv"


class PracticeRecommendationsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.compat.objective_grader_compat import (
            load_answer_key, load_submissions, grade_all, load_question_bank,
        )
        from app.application.use_cases.report_builders.knowledge_profiles import build_knowledge_profiles
        cls.ak = load_answer_key(DEMO_KEY)
        cls.subs = load_submissions(DEMO_SUB, cls.ak)
        cls.results = grade_all(cls.ak, cls.subs)
        specs_d = [_legacy_spec_to_dict(s) for s in cls.ak.questions]
        results_d = [_legacy_result_to_dict(r) for r in cls.results]
        cls.kp_rows = build_knowledge_profiles(specs_d, results_d)
        cls.bank = load_question_bank(DEMO_BANK)

    def test_matches_fixture(self):
        specs_d = [_legacy_spec_to_dict(s) for s in self.ak.questions]
        results_d = [_legacy_result_to_dict(r) for r in self.results]
        correct = build_correct_question_ids(specs_d, results_d)
        targets = build_target_difficulties(specs_d, results_d)
        bank_d = [{"question_id": q.question_id, "stem": q.stem,
                    "answer": q.answer, "tags": list(q.tags),
                    "difficulty": q.difficulty} for q in self.bank]
        rows = build_practice_recommendations(self.kp_rows, bank_d, 3, correct, targets)
        expected = json.loads((FIXTURES / "practice_recommendations.json").read_text("utf-8"))
        self.assertEqual(len(rows), len(expected))

    def test_no_legacy_import(self):
        src = Path(__file__).read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__":
    unittest.main()
