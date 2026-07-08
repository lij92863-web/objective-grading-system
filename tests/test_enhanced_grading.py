#!/usr/bin/env python3
"""Dependency-free checks for enhanced objective grading rules."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from objective_grader import (
    AnswerKey,
    QuestionSpec,
    Submission,
    competition_ranks,
    grade_all,
    mastery_level,
    normalize_answer,
    score_answer,
)


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def check_single_choice():
    spec = QuestionSpec(number=1, answers=frozenset({"A"}), points=5)
    assert_equal(score_answer(spec, normalize_answer("A")), (5, "correct"), "single choice correct")
    assert_equal(score_answer(spec, normalize_answer("B")), (0.0, "wrong"), "single choice wrong")
    assert_equal(score_answer(spec, normalize_answer("AB")), (0.0, "wrong"), "single choice multi selected")


def check_multiple_choice_two_answers():
    spec = QuestionSpec(number=2, answers=frozenset({"B", "D"}), points=6, partial_credit=True)
    assert_equal(score_answer(spec, normalize_answer("BD")), (6, "correct"), "BD full")
    assert_equal(score_answer(spec, normalize_answer("B")), (3.0, "partial"), "B partial")
    assert_equal(score_answer(spec, normalize_answer("D")), (3.0, "partial"), "D partial")
    assert_equal(score_answer(spec, normalize_answer("BCD")), (0.0, "wrong"), "BCD wrong")
    assert_equal(score_answer(spec, normalize_answer("")), (0.0, "blank"), "blank")


def check_multiple_choice_three_answers():
    spec = QuestionSpec(number=3, answers=frozenset({"A", "B", "D"}), points=6, partial_credit=True)
    assert_equal(score_answer(spec, normalize_answer("ABD")), (6, "correct"), "ABD full")
    assert_equal(score_answer(spec, normalize_answer("A")), (2.0, "partial"), "A partial")
    assert_equal(score_answer(spec, normalize_answer("AB")), (4.0, "partial"), "AB partial")
    assert_equal(score_answer(spec, normalize_answer("AD")), (4.0, "partial"), "AD partial")
    assert_equal(score_answer(spec, normalize_answer("AC")), (0.0, "wrong"), "AC wrong")
    assert_equal(score_answer(spec, normalize_answer("ABCD")), (0.0, "wrong"), "ABCD wrong")


def check_special_statuses():
    cancelled = QuestionSpec(number=4, answers=frozenset({"A"}), points=5, status="cancelled")
    bonus_all = QuestionSpec(number=5, answers=frozenset({"A"}), points=5, status="bonus_all")
    bonus_if_answered = QuestionSpec(number=6, answers=frozenset({"A"}), points=5, status="bonus_if_answered")
    assert_equal(AnswerKey((cancelled, bonus_all, bonus_if_answered)).total_points, 10, "cancelled excluded")
    assert_equal(score_answer(cancelled, normalize_answer("A")), (0.0, "cancelled"), "cancelled status")
    assert_equal(score_answer(bonus_all, normalize_answer("")), (5, "bonus"), "bonus_all")
    assert_equal(score_answer(bonus_if_answered, normalize_answer("B")), (5, "bonus"), "bonus_if_answered answered")
    assert_equal(score_answer(bonus_if_answered, normalize_answer("")), (0.0, "blank"), "bonus_if_answered blank")


def check_ranking():
    key = AnswerKey((QuestionSpec(number=1, answers=frozenset({"A"}), points=10),))
    submissions = [
        Submission("S1", "One", {1: normalize_answer("A")}, {1: "A"}, (), 2),
        Submission("S2", "Two", {1: normalize_answer("A")}, {1: "A"}, (), 3),
        Submission("S3", "Three", {1: normalize_answer("B")}, {1: "B"}, (), 4),
    ]
    ranks = competition_ranks(grade_all(key, submissions))
    assert_equal(ranks, [1, 1, 3], "competition ranking")


def check_mastery_levels():
    assert_equal(mastery_level(30), "严重薄弱", "mastery 30")
    assert_equal(mastery_level(50), "明显薄弱", "mastery 50")
    assert_equal(mastery_level(70), "基本掌握", "mastery 70")
    assert_equal(mastery_level(90), "掌握较好", "mastery 90")


def check_answer_aliases():
    spec = QuestionSpec(
        number=9,
        answers=normalize_answer("1/2"),
        points=5,
        answer_text="1/2",
        answer_aliases=("0.5", r"\frac{1}{2}"),
        tolerance=0.001,
    )
    assert_equal(score_answer(spec, normalize_answer("0.5"), "0.5"), (5, "correct"), "alias decimal")
    assert_equal(score_answer(spec, normalize_answer("0.5004"), "0.5004"), (5, "correct"), "tolerance decimal")
    assert_equal(score_answer(spec, normalize_answer("0.501"), "0.501"), (5, "correct"), "tolerance boundary")


def check_text_answer_status():
    spec = QuestionSpec(number=10, answers=normalize_answer("函数"), points=5, answer_text="函数")
    assert_equal(score_answer(spec, normalize_answer("导数"), "导数"), (0.0, "wrong"), "text mismatch is wrong")

    choice = QuestionSpec(number=11, answers=frozenset({"A"}), points=5, answer_text="A")
    assert_equal(score_answer(choice, normalize_answer("I"), "I"), (0.0, "invalid"), "choice illegal option is invalid")


def main():
    check_single_choice()
    check_multiple_choice_two_answers()
    check_multiple_choice_three_answers()
    check_special_statuses()
    check_ranking()
    check_mastery_levels()
    check_answer_aliases()
    check_text_answer_status()
    print("enhanced grading tests passed")


if __name__ == "__main__":
    main()
