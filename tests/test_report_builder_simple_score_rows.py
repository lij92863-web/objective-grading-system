"""Simple score rows builder — fixture baseline (B4)."""
import json, ast, unittest
from pathlib import Path
from app.application.use_cases.report_builders.score_rows import build_simple_score_rows
from app.application.use_cases.csv_report_pipeline import _legacy_result_to_dict

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"
DEMO_KEY = Path(__file__).parents[1] / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = Path(__file__).parents[1] / "samples/demo_exam/submissions_sample.csv"


class SimpleScoreRowsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.compat.objective_grader_compat import load_answer_key, load_submissions, grade_all
        cls.ak = load_answer_key(DEMO_KEY)
        cls.subs = load_submissions(DEMO_SUB, cls.ak)
        cls.results = grade_all(cls.ak, cls.subs)

    def test_field_order(self):
        fields = ["rank","student_id","name","score","max_score","percent",
                   "correct_count","wrong_or_partial_count","blank_count",
                   "invalid_count","wrong_questions","blank_questions","remark"]
        rows = build_simple_score_rows([_legacy_result_to_dict(r) for r in self.results])
        self.assertGreater(len(rows), 0)
        self.assertEqual(list(rows[0].keys()), fields)

    def test_matches_fixture(self):
        rows = build_simple_score_rows([_legacy_result_to_dict(r) for r in self.results])
        expected = json.loads((FIXTURES/"simple_score_rows.json").read_text("utf-8"))
        self.assertEqual(len(rows), len(expected))
        for r, e in zip(rows, expected):
            self.assertEqual(str(r["student_id"]), str(e["student_id"]))

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
