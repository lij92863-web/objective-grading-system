import ast
import unittest
from pathlib import Path

from legacy.objective_grader_legacy import (
    basic_stats as legacy_basic_stats,
    grade_all,
    load_answer_key,
    load_submissions,
)

from app.application.use_cases.report_builders.basic_stats import basic_stats


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class BasicStatsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists() or not DEMO_SUB.exists():
            raise unittest.SkipTest("demo samples are unavailable")
        answer_key = load_answer_key(DEMO_KEY)
        cls.results = grade_all(answer_key, load_submissions(DEMO_SUB, answer_key))

    def test_matches_legacy(self):
        self.assertEqual(basic_stats(self.results), legacy_basic_stats(self.results))

    def test_empty_matches_legacy(self):
        self.assertEqual(basic_stats([]), legacy_basic_stats([]))

    def test_dict_input_matches_object_input(self):
        dict_results = [
            {"score": result.score, "percent": result.percent}
            for result in self.results
        ]
        self.assertEqual(basic_stats(dict_results), legacy_basic_stats(self.results))

    def test_no_legacy_import(self):
        source_path = PROJECT_ROOT / "app/application/use_cases/report_builders/basic_stats.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            self.assertFalse(any(name == "legacy" or name.startswith("legacy.") for name in names))


if __name__ == "__main__":
    unittest.main()
