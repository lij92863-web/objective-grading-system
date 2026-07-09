"""Basic stats builder — fixture baseline (B4)."""
import json, ast, unittest
from pathlib import Path
from app.application.use_cases.report_builders.basic_stats import basic_stats

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"
DEMO_KEY = Path(__file__).parents[1] / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = Path(__file__).parents[1] / "samples/demo_exam/submissions_sample.csv"


class BasicStatsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.compat.objective_grader_compat import load_answer_key, load_submissions, grade_all
        ak = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, ak)
        cls.results = grade_all(ak, subs)

    def test_matches_fixture(self):
        stats = basic_stats(self.results)
        expected = json.loads((FIXTURES/"basic_stats.json").read_text("utf-8"))
        self.assertEqual(stats["average"], float(expected["average"]))

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
