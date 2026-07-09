import ast
import unittest
from pathlib import Path

from legacy.objective_grader_legacy import (
    QuestionResult,
    StudentResult,
    grade_all,
    load_answer_key,
    load_submissions,
    simple_score_rows as legacy_simple_score_rows,
)

from app.application.use_cases.report_builders.simple_score_rows import (
    build_simple_score_rows,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
BUILDER_PATH = (
    PROJECT_ROOT
    / "app/application/use_cases/report_builders/simple_score_rows.py"
)


def _result_to_dict(result):
    return {
        "student_id": result.student_id,
        "name": result.name,
        "score": result.score,
        "max_score": result.max_score,
        "percent": result.percent,
        "correct_count": result.correct_count,
        "wrong_or_partial_count": result.wrong_or_partial_count,
        "blank_count": result.blank_count,
        "invalid_count": result.invalid_count,
        "details": [
            {
                "number": detail.number,
                "status": detail.status,
                "score": detail.score,
                "max_score": detail.max_score,
            }
            for detail in result.details
        ],
    }


class SimpleScoreRowsBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo samples")
        key = load_answer_key(DEMO_KEY)
        submissions = load_submissions(DEMO_SUB, key)
        cls.results = grade_all(key, submissions)

    def test_demo_data_matches_legacy_rows(self):
        legacy_rows = legacy_simple_score_rows(self.results)
        new_rows = build_simple_score_rows([
            _result_to_dict(result) for result in self.results
        ])

        self.assertEqual(legacy_rows, new_rows)
        self.assertGreater(len(new_rows), 0)
        self.assertEqual(list(legacy_rows[0]), list(new_rows[0]))
        self.assertEqual(legacy_rows[0], new_rows[0])
        self.assertEqual(legacy_rows[-1], new_rows[-1])

    def test_chinese_name_is_preserved(self):
        detail = QuestionResult(
            number=1,
            expected=frozenset({"A"}),
            actual=frozenset({"A"}),
            raw_actual="A",
            score=1,
            max_score=1,
            status="correct",
        )
        result = StudentResult(
            student_id="cn-1",
            name="张三",
            score=1,
            max_score=1,
            percent=100,
            correct_count=1,
            wrong_or_partial_count=0,
            blank_count=0,
            invalid_count=0,
            details=(detail,),
        )

        self.assertEqual(
            legacy_simple_score_rows([result]),
            build_simple_score_rows([_result_to_dict(result)]),
        )

    def test_tied_scores_keep_competition_rank_behavior(self):
        detail = QuestionResult(
            number=1,
            expected=frozenset({"A"}),
            actual=frozenset({"A"}),
            raw_actual="A",
            score=1,
            max_score=1,
            status="correct",
        )
        results = [
            StudentResult("1", "A", 8, 10, 80, 1, 0, 0, 0, (detail,)),
            StudentResult("2", "B", 8, 10, 80, 1, 0, 0, 0, (detail,)),
            StudentResult("3", "C", 7, 10, 70, 1, 0, 0, 0, (detail,)),
        ]

        rows = build_simple_score_rows([_result_to_dict(r) for r in results])

        self.assertEqual([1, 1, 3], [row["rank"] for row in rows])
        self.assertEqual(legacy_simple_score_rows(results), rows)

    def test_empty_submissions_match_legacy(self):
        self.assertEqual([], build_simple_score_rows([]))
        self.assertEqual(legacy_simple_score_rows([]), build_simple_score_rows([]))

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
