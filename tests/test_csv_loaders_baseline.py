import os
import tempfile
import unittest
from pathlib import Path

from legacy.objective_grader_legacy import load_answer_key, load_submissions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class LegacyCsvLoadersBaselineTests(unittest.TestCase):
    def test_demo_answer_key_loads(self):
        key = load_answer_key(DEMO_KEY)

        self.assertGreater(len(key.questions), 0)
        self.assertTrue(hasattr(key, "by_number"))
        self.assertTrue(hasattr(key, "total_points"))
        first = key.questions[0]
        for attr in ("number", "answers", "points", "tags", "status"):
            self.assertTrue(hasattr(first, attr), attr)

    def test_demo_submissions_load(self):
        key = load_answer_key(DEMO_KEY)
        submissions = load_submissions(DEMO_SUB, key)

        self.assertGreater(len(submissions), 0)
        first = submissions[0]
        for attr in (
            "student_id",
            "name",
            "answers",
            "raw_answers",
            "extra_questions",
            "row_number",
        ):
            self.assertTrue(hasattr(first, attr), attr)

    def test_chinese_and_blank_cells_behavior(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "data") as tmp:
            tmp_path = Path(tmp)
            key_path = tmp_path / "answer_key.csv"
            sub_path = tmp_path / "submissions.csv"
            key_path.write_text(
                "question,answer,points,tags\n"
                "1,A,1,中文标签\n"
                "2,,1,\n",
                encoding="utf-8-sig",
            )
            sub_path.write_text(
                "student_id,name,Q1,Q2\n"
                "001,张三,A,\n",
                encoding="utf-8-sig",
            )

            key = load_answer_key(key_path)
            submissions = load_submissions(sub_path, key)

            self.assertEqual(("中文标签",), key.questions[0].tags)
            self.assertEqual(frozenset(), key.questions[1].answers)
            self.assertEqual("张三", submissions[0].name)
            self.assertEqual(frozenset(), submissions[0].answers[2])
            self.assertEqual("", submissions[0].raw_answers[2])

    def test_missing_file_behavior(self):
        missing = PROJECT_ROOT / "data" / "missing_loader_baseline.csv"

        with self.assertRaises(FileNotFoundError):
            load_answer_key(missing)

    def test_missing_question_field_behavior(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "data") as tmp:
            key_path = Path(tmp) / "answer_key.csv"
            key_path.write_text("answer\nA\n", encoding="utf-8-sig")

            with self.assertRaises(ValueError):
                load_answer_key(key_path)

    def test_no_env_access_marker(self):
        before = dict(os.environ)
        load_answer_key(DEMO_KEY)
        self.assertEqual(before, dict(os.environ))


if __name__ == "__main__":
    unittest.main()
