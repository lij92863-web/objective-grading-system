import ast
import unittest
from pathlib import Path

from legacy.objective_grader_legacy import grade_all as legacy_grade_all

from app.domain.grading import grade_all as domain_grade_all
from app.infrastructure.loaders.csv_loaders import load_answer_key, load_submissions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


def result_signature(result):
    return (
        result.student_id,
        result.name,
        result.score,
        result.max_score,
        result.percent,
        result.correct_count,
        result.wrong_or_partial_count,
        result.blank_count,
        result.invalid_count,
        tuple(
            (
                detail.number,
                detail.expected,
                detail.actual,
                detail.raw_actual,
                detail.score,
                detail.max_score,
                detail.status,
            )
            for detail in result.details
        ),
    )


class GradingCoreEntryBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists() or not DEMO_SUB.exists():
            raise unittest.SkipTest("demo samples are unavailable")
        cls.answer_key = load_answer_key(DEMO_KEY)
        cls.submissions = load_submissions(DEMO_SUB, cls.answer_key)

    def test_domain_grade_all_matches_legacy_on_demo(self):
        legacy_results = legacy_grade_all(self.answer_key, self.submissions)
        domain_results = domain_grade_all(self.answer_key, self.submissions)
        self.assertEqual(
            [result_signature(result) for result in domain_results],
            [result_signature(result) for result in legacy_results],
        )

    def test_domain_grading_imports_no_legacy(self):
        for source_path in (PROJECT_ROOT / "app/domain/grading").glob("*.py"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                self.assertFalse(
                    any(name == "legacy" or name.startswith("legacy.") for name in names),
                    source_path.name,
                )


if __name__ == "__main__":
    unittest.main()
