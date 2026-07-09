import ast
import tempfile
import unittest
from pathlib import Path

from app.compat.objective_grader_compat import (
    load_answer_key as legacy_load_answer_key,
    load_submissions as legacy_load_submissions,
)

from app.infrastructure.loaders.csv_loaders import (
    load_answer_key,
    load_submissions,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
LOADER_PATH = PROJECT_ROOT / "app/infrastructure/loaders/csv_loaders.py"


def question_to_tuple(question):
    return (
        question.number,
        question.answers,
        question.points,
        question.partial_credit,
        question.partial_points,
        question.tags,
        question.source_id,
        question.difficulty,
        question.answer_text,
        question.answer_aliases,
        question.tolerance,
        question.status,
    )


def answer_key_to_tuple(answer_key):
    return (
        tuple(question_to_tuple(question) for question in answer_key.questions),
        answer_key.duplicate_questions,
        answer_key.total_points,
        tuple(sorted(answer_key.by_number)),
    )


def submission_to_tuple(submission):
    return (
        submission.student_id,
        submission.name,
        submission.answers,
        submission.raw_answers,
        submission.extra_questions,
        submission.row_number,
    )


class CsvLoadersTests(unittest.TestCase):
    def test_demo_answer_key_matches_legacy(self):
        self.assertEqual(
            answer_key_to_tuple(legacy_load_answer_key(DEMO_KEY)),
            answer_key_to_tuple(load_answer_key(DEMO_KEY)),
        )

    def test_demo_submissions_match_legacy(self):
        legacy_key = legacy_load_answer_key(DEMO_KEY)
        new_key = load_answer_key(DEMO_KEY)

        self.assertEqual(
            tuple(submission_to_tuple(s) for s in legacy_load_submissions(
                DEMO_SUB, legacy_key
            )),
            tuple(submission_to_tuple(s) for s in load_submissions(
                DEMO_SUB, new_key
            )),
        )

    def test_chinese_and_blank_cells_match_legacy(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "data") as tmp:
            tmp_path = Path(tmp)
            key_path = tmp_path / "answer_key.csv"
            sub_path = tmp_path / "submissions.csv"
            key_path.write_text(
                "题号,答案,分值,知识点\n"
                "1,A,1,中文标签\n"
                "2,,1,\n",
                encoding="utf-8-sig",
            )
            sub_path.write_text(
                "学号,姓名,题1,题2\n"
                "001,张三,A,\n",
                encoding="utf-8-sig",
            )
            legacy_key = legacy_load_answer_key(key_path)
            new_key = load_answer_key(key_path)

            self.assertEqual(
                answer_key_to_tuple(legacy_key),
                answer_key_to_tuple(new_key),
            )
            self.assertEqual(
                tuple(submission_to_tuple(s) for s in legacy_load_submissions(
                    sub_path, legacy_key
                )),
                tuple(submission_to_tuple(s) for s in load_submissions(
                    sub_path, new_key
                )),
            )

    def test_missing_file_matches_legacy(self):
        missing = PROJECT_ROOT / "data" / "missing_loader_migration.csv"

        with self.assertRaises(FileNotFoundError):
            legacy_load_answer_key(missing)
        with self.assertRaises(FileNotFoundError):
            load_answer_key(missing)

    def test_missing_question_field_matches_legacy(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "data") as tmp:
            key_path = Path(tmp) / "answer_key.csv"
            key_path.write_text("answer\nA\n", encoding="utf-8-sig")

            with self.assertRaises(ValueError):
                legacy_load_answer_key(key_path)
            with self.assertRaises(ValueError):
                load_answer_key(key_path)

    def test_infrastructure_boundary_imports(self):
        tree = ast.parse(LOADER_PATH.read_text(encoding="utf-8"))
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
