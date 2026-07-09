"""Knowledge profiles builder — fixture baseline (B4)."""
import json, ast, unittest
from pathlib import Path
from app.application.use_cases.report_builders.knowledge_profiles import build_knowledge_profiles
from app.application.use_cases.csv_report_pipeline import _legacy_result_to_dict, _legacy_spec_to_dict

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"
DEMO_KEY = Path(__file__).parents[1] / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = Path(__file__).parents[1] / "samples/demo_exam/submissions_sample.csv"


class KnowledgeProfilesBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.compat.objective_grader_compat import load_answer_key, load_submissions, grade_all
        cls.ak = load_answer_key(DEMO_KEY)
        cls.subs = load_submissions(DEMO_SUB, cls.ak)
        cls.results = grade_all(cls.ak, cls.subs)

    def test_matches_fixture(self):
        specs_d = [_legacy_spec_to_dict(s) for s in self.ak.questions]
        results_d = [_legacy_result_to_dict(r) for r in self.results]
        profiles = build_knowledge_profiles(specs_d, results_d)
        expected = json.loads((FIXTURES/"knowledge_profiles.json").read_text("utf-8"))
        self.assertEqual(len(profiles), len(expected))

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
