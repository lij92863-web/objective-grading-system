"""Class report builder — fixture baseline (B4)."""
import json, ast, unittest
from pathlib import Path
from app.application.use_cases.report_builders.class_report import build_class_report
from app.application.use_cases.csv_report_pipeline import _legacy_result_to_dict, _legacy_spec_to_dict

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"
DEMO_KEY = Path(__file__).parents[1] / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = Path(__file__).parents[1] / "samples/demo_exam/submissions_sample.csv"


class ClassReportBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.compat.objective_grader_compat import load_answer_key, load_submissions, grade_all
        cls.ak = load_answer_key(DEMO_KEY)
        cls.subs = load_submissions(DEMO_SUB, cls.ak)
        cls.results = grade_all(cls.ak, cls.subs)

    def test_matches_fixture(self):
        from app.application.use_cases.report_builders.knowledge_profiles import build_knowledge_profiles
        specs_d = [_legacy_spec_to_dict(s) for s in self.ak.questions]
        results_d = [_legacy_result_to_dict(r) for r in self.results]
        profiles = build_knowledge_profiles(specs_d, results_d)
        profiles_d = [{"student_id": p["student_id"], "name": p["name"], "tag": p["tag"],
                        "score": p["score"], "max_score": p["max_score"], "mastery": p["mastery"],
                        "question_count": p["question_count"], "weak": p["weak"],
                        "mastery_level": p["mastery_level"]} for p in profiles]
        meta = {"exam_name": "fixture", "class_name": "Test", "subject": "Math",
                "exam_date": "2026-07-09"}
        rows = build_class_report(meta, specs_d, results_d, profiles_d)
        expected = json.loads((FIXTURES / "class_report.json").read_text("utf-8"))
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
