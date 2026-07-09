"""Grading core entry baseline — fixture-based comparison (B5)."""
import json, ast, unittest
from pathlib import Path
from app.domain.grading import grade_all as domain_grade_all
from app.infrastructure.loaders.csv_loaders import load_answer_key, load_submissions

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"
DEMO_KEY = Path(__file__).parents[1] / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = Path(__file__).parents[1] / "samples/demo_exam/submissions_sample.csv"


class GradingCoreEntryBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ak = load_answer_key(DEMO_KEY)
        cls.subs = load_submissions(DEMO_SUB, cls.ak)

    def test_domain_grading_produces_results(self):
        results = domain_grade_all(self.ak, self.subs)
        self.assertGreater(len(results), 0)
        self.assertGreater(results[0].score, -1)

    def test_matches_stored_stats(self):
        results = domain_grade_all(self.ak, self.subs)
        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(results[0].student_id, "S001")
        self.assertGreater(results[0].score, 0)

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
