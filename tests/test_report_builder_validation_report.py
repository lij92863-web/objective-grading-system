"""Validation report builder — fixture baseline (B4)."""
import json, ast, unittest
from pathlib import Path
from app.application.use_cases.report_builders.validation_report import build_validation_report
from app.application.use_cases.csv_report_pipeline import _legacy_result_to_dict, _legacy_spec_to_dict, _legacy_sub_to_dict

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"
DEMO_KEY = Path(__file__).parents[1] / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = Path(__file__).parents[1] / "samples/demo_exam/submissions_sample.csv"


class ValidationReportBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.compat.objective_grader_compat import load_answer_key, load_submissions, grade_all
        from app.application.use_cases.report_builders.knowledge_profiles import build_knowledge_profiles
        cls.ak = load_answer_key(DEMO_KEY)
        cls.subs = load_submissions(DEMO_SUB, cls.ak)
        cls.results = grade_all(cls.ak, cls.subs)
        specs_d = [_legacy_spec_to_dict(s) for s in cls.ak.questions]
        results_d = [_legacy_result_to_dict(r) for r in cls.results]
        cls.profiles = build_knowledge_profiles(specs_d, results_d)

    def test_matches_fixture(self):
        ak_dict = {"by_number": {s.number: {"question": s.number, "source_id": s.source_id,
            "tags": list(s.tags), "status": s.status, "points": s.points}
            for s in self.ak.questions}, "questions": [{"question": s.number,
            "source_id": s.source_id, "tags": list(s.tags), "status": s.status,
            "points": s.points} for s in self.ak.questions], "duplicate_questions": []}
        subs_d = [_legacy_sub_to_dict(s) for s in self.subs]
        results_d = [_legacy_result_to_dict(r) for r in self.results]
        profiles_d = [{"student_id": p["student_id"], "name": p["name"], "tag": p["tag"],
                        "score": p["score"], "max_score": p["max_score"], "mastery": p["mastery"],
                        "question_count": p["question_count"], "weak": p["weak"],
                        "mastery_level": p["mastery_level"]} for p in self.profiles]
        rows = build_validation_report(ak_dict, subs_d, results_d, profiles_d, None)
        expected = json.loads((FIXTURES / "validation_report.json").read_text("utf-8"))
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
