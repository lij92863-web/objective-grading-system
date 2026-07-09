import ast
import unittest
from pathlib import Path

from legacy.objective_grader_legacy import (
    QuestionResult,
    StudentResult,
    grade_all,
    item_stats as legacy_item_stats,
    load_answer_key,
    load_submissions,
)

from app.application.use_cases.report_builders.item_stats import (
    build_item_stats,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
BUILDER_PATH = (
    PROJECT_ROOT / "app/application/use_cases/report_builders/item_stats.py"
)


class ItemStatsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo samples")
        cls.key = load_answer_key(DEMO_KEY)
        submissions = load_submissions(DEMO_SUB, cls.key)
        cls.results = grade_all(cls.key, submissions)

    def test_demo_data_matches_legacy_rows(self):
        legacy_rows = legacy_item_stats(self.key, self.results)
        new_rows = build_item_stats(self.key, self.results)

        self.assertEqual(legacy_rows, new_rows)
        self.assertGreater(len(new_rows), 0)
        self.assertEqual(list(legacy_rows[0]), list(new_rows[0]))
        self.assertEqual(legacy_rows[0], new_rows[0])
        self.assertEqual(legacy_rows[-1], new_rows[-1])

    def test_blank_wrong_partial_invalid_distribution_match_legacy(self):
        spec = self.key.questions[0]
        details = [
            QuestionResult(
                spec.number, frozenset({"A"}), frozenset({"A"}),
                "A", 1, 1, "correct",
            ),
            QuestionResult(
                spec.number, frozenset({"A"}), frozenset(),
                "", 0, 1, "blank",
            ),
            QuestionResult(
                spec.number, frozenset({"A"}), frozenset({"B"}),
                "B", 0, 1, "wrong",
            ),
            QuestionResult(
                spec.number, frozenset({"A"}), frozenset({"A", "B"}),
                "AB", 0.5, 1, "partial",
            ),
            QuestionResult(
                spec.number, frozenset({"A"}), frozenset({"Z"}),
                "Z", 0, 1, "invalid",
            ),
        ]
        results = [
            StudentResult(
                str(index), f"S{index}", detail.score, detail.max_score,
                detail.score * 100, 0, 0, 0, 0, (detail,),
            )
            for index, detail in enumerate(details, start=1)
        ]

        self.assertEqual(
            legacy_item_stats(type("Key", (), {"questions": (spec,)})(), results),
            build_item_stats({"questions": [spec]}, results),
        )

    def test_empty_results_match_legacy(self):
        self.assertEqual(
            legacy_item_stats(self.key, []),
            build_item_stats(self.key, []),
        )

    def test_application_boundary_imports(self):
        tree = ast.parse(BUILDER_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertFalse(alias.name.startswith("legacy"))
                    self.assertFalse(alias.name.startswith("web"))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                self.assertFalse(module.startswith("legacy"))
                self.assertFalse(module.startswith("web"))


if __name__ == "__main__":
    unittest.main()
