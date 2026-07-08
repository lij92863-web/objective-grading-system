#!/usr/bin/env python3
"""Unified lightweight test runner for the objective grading project."""

import csv
import tempfile
import unittest
from pathlib import Path

import objective_grader as grader
import roster_manager
from app.validators import has_blocking_errors
from app.workflow import run_grading
from app.data_io import parse_answer_source, review_rows_to_answer_key_csv


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


class GradingRuleTests(unittest.TestCase):
    def test_single_choice_scoring(self):
        spec = grader.QuestionSpec(number=1, answers=frozenset({"A"}), points=5)
        self.assertEqual(grader.score_answer(spec, grader.normalize_answer("A")), (5, "correct"))
        self.assertEqual(grader.score_answer(spec, grader.normalize_answer("B")), (0.0, "wrong"))

    def test_multiple_choice_partial_credit(self):
        spec = grader.QuestionSpec(number=2, answers=frozenset({"B", "D"}), points=6, partial_credit=True)
        self.assertEqual(grader.score_answer(spec, grader.normalize_answer("B")), (3.0, "partial"))
        self.assertEqual(grader.score_answer(spec, grader.normalize_answer("BCD")), (0.0, "wrong"))

    def test_blank_equivalent_answer_and_tolerance(self):
        spec = grader.QuestionSpec(
            number=3,
            answers=grader.normalize_answer("1/2"),
            points=4,
            answer_text="1/2",
            answer_aliases=("0.5",),
            tolerance=0.001,
        )
        self.assertEqual(grader.score_answer(spec, grader.normalize_answer("0.5004"), "0.5004"), (4, "correct"))

    def test_special_statuses(self):
        cancelled = grader.QuestionSpec(number=4, answers=frozenset({"A"}), points=5, status="cancelled")
        bonus_all = grader.QuestionSpec(number=5, answers=frozenset({"A"}), points=5, status="bonus_all")
        bonus_if_answered = grader.QuestionSpec(number=6, answers=frozenset({"A"}), points=5, status="bonus_if_answered")
        self.assertEqual(grader.score_answer(cancelled, grader.normalize_answer("A")), (0.0, "cancelled"))
        self.assertEqual(grader.score_answer(bonus_all, grader.normalize_answer("")), (5, "bonus"))
        self.assertEqual(grader.score_answer(bonus_if_answered, grader.normalize_answer("B")), (5, "bonus"))

    def test_invalid_answer(self):
        spec = grader.QuestionSpec(number=7, answers=frozenset({"A"}), points=2, answer_text="A")
        self.assertEqual(grader.score_answer(spec, grader.normalize_answer("I"), "I"), (0.0, "invalid"))


class FileWorkflowTests(unittest.TestCase):
    def test_answer_source_csv_and_text_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "answer.csv"
            text_path = root / "answer.txt"
            write_text(csv_path, "question,answer,points\n1,A,1\n2,BD,2\n")
            write_text(text_path, "1.A\n2.B\n3.CD\n")
            csv_draft = parse_answer_source(csv_path)
            text_draft = parse_answer_source(text_path)
            self.assertEqual(len(csv_draft["items"]), 2)
            self.assertEqual(len(text_draft["items"]), 3)
            answer_key = root / "confirmed_answer_key.csv"
            review_rows_to_answer_key_csv(csv_draft["items"], answer_key)
            self.assertTrue(answer_key.exists())

    def test_duplicate_question_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / "answer_key.csv"
            submissions = root / "submissions.csv"
            out_dir = root / "reports"
            write_text(key, "question,answer,points\n1,A,1\n1,B,1\n")
            write_text(submissions, "student_id,name,Q1\nS1,One,A\n")
            result = run_grading(key, submissions, out_dir, no_archive=True)
            self.assertFalse(result["ok"])
            self.assertTrue((out_dir / "validation_report.csv").exists())
            self.assertTrue((out_dir / "error_report.html").exists())

    def test_duplicate_student_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / "answer_key.csv"
            submissions = root / "submissions.csv"
            write_text(key, "question,answer,points\n1,A,1\n")
            write_text(submissions, "student_id,name,Q1\nS1,One,A\nS1,One Again,B\n")
            answer_key = grader.load_answer_key(key)
            loaded = grader.load_submissions(submissions, answer_key)
            results = grader.grade_all(answer_key, loaded)
            profiles = grader.build_knowledge_profiles(answer_key, results)
            rows = grader.build_validation_report(answer_key, loaded, results, profiles)
            self.assertTrue(any(row["scope"] == "submission" and row["severity"] == "warning" for row in rows))

    def test_empty_submissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / "answer_key.csv"
            submissions = root / "submissions.csv"
            out_dir = root / "reports"
            write_text(key, "question,answer,points\n1,A,1\n")
            write_text(submissions, "student_id,name,Q1\n")
            result = run_grading(key, submissions, out_dir, no_archive=True, allow_errors=True)
            self.assertTrue(result["ok"])
            self.assertTrue((out_dir / "summary.csv").exists())

    def test_roster_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_file = root / "roster.csv"
            classes_root = root / "classes"
            write_text(roster_file, "student_id,name\nS1,One\nS2,Two\n")
            result = roster_manager.import_roster(roster_file, "TestClass", classes_root=classes_root)
            self.assertEqual(result["student_count"], 2)
            self.assertEqual(roster_manager.load_roster("TestClass", classes_root=classes_root)["S1"], "One")

    def test_validation_blocking_helper(self):
        rows = [{"severity": "error", "scope": "answer_key", "item": "Q1", "message": "duplicate"}]
        self.assertTrue(has_blocking_errors(rows))

    def test_run_id_archive_prevents_overwrite_and_reports_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / "answer_key.csv"
            submissions = root / "submissions.csv"
            reports = root / "reports"
            archive = root / "archive"
            write_text(key, "question,answer,points,tags,difficulty\n1,A,1,tag1,1\n2,BD,2,tag2,2\n")
            write_text(submissions, "student_id,name,Q1,Q2\nS1,One,A,B\nS2,Two,B,BD\n")
            first = run_grading(key, submissions, reports, archive_root=archive, run_id="20260101_010101")
            second = run_grading(key, submissions, reports, archive_root=archive, run_id="20260101_010102")
            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertNotEqual(first["archived_dir"], second["archived_dir"])
            for name in [
                "summary.csv",
                "detail.csv",
                "item_analysis.csv",
                "knowledge_profile.csv",
                "teaching_plan.csv",
                "class_remedial_package.csv",
                "layered_remedial_plan.csv",
                "exam_report.xlsx",
                "index.html",
            ]:
                self.assertTrue((reports / name).exists(), name)

    def test_recognized_submissions_conversion_shape(self):
        import grade_exam_workflow

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            recognized = root / "recognized.csv"
            submissions = root / "submissions.csv"
            unmatched = root / "unmatched.csv"
            key = root / "answer_key.csv"
            write_text(key, "question,answer,points\n1,A,1\n")
            write_text(recognized, "recognized_student_id,Q1\nS1,A\n")

            old_match = grade_exam_workflow.match_student
            old_load = grade_exam_workflow.load_roster
            try:
                grade_exam_workflow.load_roster = lambda class_name: {"S1": "One"}
                grade_exam_workflow.match_student = lambda class_name, student_id: {
                    "matched": True,
                    "student_id": student_id,
                    "name": "One",
                    "message": "",
                }
                result = grade_exam_workflow.convert_recognized_submissions("Test", recognized, submissions, unmatched, key)
            finally:
                grade_exam_workflow.match_student = old_match
                grade_exam_workflow.load_roster = old_load
            self.assertEqual(result["matched_count"], 1)
            with submissions.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["student_id"], "S1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
