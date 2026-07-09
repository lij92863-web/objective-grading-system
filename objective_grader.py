#!/usr/bin/env python3
"""Command-line entry for the objective-question grader.

The grading implementation now lives behind ``workflow.run_grading`` and the
small modules under ``core/``, ``analysis/``, and ``reports/``. Public symbols
from the previous single-file implementation are re-exported for compatibility
with older scripts and tests.
"""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional

from legacy import objective_grader_legacy as legacy
from app.workflow import run_grading

COMPAT_EXPORTS = (
    "AnswerKey",
    "BankQuestion",
    "CHOICE_OPTIONS",
    "Counter",
    "Dict",
    "EPSILON",
    "ExamMeta",
    "FIELD_ALIASES",
    "FrozenSet",
    "Iterable",
    "KnowledgeProfile",
    "List",
    "OPTION_RE",
    "Optional",
    "Path",
    "QUESTION_RE",
    "QUESTION_STATUSES",
    "QuestionResult",
    "QuestionSpec",
    "Set",
    "StudentResult",
    "Submission",
    "TRUTHY",
    "Tuple",
    "advanced_dashboard_css",
    "allowed_options",
    "archive_reports",
    "argparse",
    "bar",
    "basic_stats",
    "build_abnormal_items",
    "build_class_report",
    "build_correct_question_ids",
    "build_knowledge_profiles",
    "build_parser",
    "build_question_accuracy_items",
    "build_score_distribution",
    "build_target_difficulties",
    "build_teaching_suggestions",
    "build_validation_report",
    "build_weak_items",
    "build_weak_tags",
    "competition_ranks",
    "create_sample_files",
    "csv",
    "dataclasses",
    "date",
    "datetime",
    "defaultdict",
    "difficulty_rank",
    "escape",
    "excel_column_name",
    "first_present",
    "format_answer",
    "format_expected_answer",
    "get_rate_class",
    "grade_all",
    "grade_submission",
    "html_escape",
    "is_choice_answer",
    "is_choice_like_answer",
    "item_stats",
    "json",
    "load_answer_key",
    "load_question_bank",
    "load_submissions",
    "main",
    "main_wrong_answer",
    "mastery_level",
    "matches_text_answer",
    "normalize_answer",
    "normalize_text_answer",
    "numeric_value",
    "parse_bool",
    "parse_difficulty",
    "parse_optional_float",
    "parse_question_number",
    "parse_status",
    "pct",
    "percent",
    "print_console_report",
    "re",
    "read_csv",
    "read_csv_for_workbook",
    "recommend_practice",
    "render_abnormal_table",
    "render_horizontal_bar_chart",
    "render_metric_cards",
    "render_option_distribution",
    "render_suggestion_cards",
    "render_table",
    "render_vertical_bar_chart",
    "render_wrong_top",
    "report_css",
    "report_link",
    "safe_slug",
    "score_answer",
    "score_answer_detail",
    "score_bands",
    "shutil",
    "simple_score_rows",
    "split_aliases",
    "split_tags",
    "statistics",
    "student_status_map",
    "sys",
    "worksheet_xml",
    "write_advanced_dashboard",
    "write_class_report",
    "write_detail",
    "write_dicts",
    "write_dicts_with_fields",
    "write_item_analysis",
    "write_knowledge_profiles",
    "write_practice_recommendations",
    "write_report_index",
    "write_simple_report",
    "write_simple_score_workbook",
    "write_student_report",
    "write_summary",
    "write_validation_report",
    "write_workbook",
    "write_xlsx",
    "xml_attr",
    "zipfile",
)

globals().update({name: getattr(legacy, name) for name in COMPAT_EXPORTS})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grade objective-question submissions from CSV files.")
    parser.add_argument("--answer-key", type=Path, help="CSV answer key file.")
    parser.add_argument("--submissions", type=Path, help="CSV student submissions file.")
    parser.add_argument("--question-bank", type=Path, help="Optional CSV question bank for recommendations.")
    parser.add_argument("--out-dir", type=Path, default=Path("data") / "reports" / "latest", help="Directory for exported reports.")
    parser.add_argument("--make-samples", action="store_true", help="Create sample CSV files in the output directory.")
    parser.add_argument("--weak-threshold", type=float, default=70.0, help="Mastery percentage below this value is treated as weak.")
    parser.add_argument("--practice-per-tag", type=int, default=3, help="Recommended practice questions per weak knowledge point.")
    parser.add_argument("--exam-name", default="demo_exam", help="Exam name used in class reports and archives.")
    parser.add_argument("--class-name", default="", help="Class name used in class reports and archives.")
    parser.add_argument("--subject", default="", help="Subject name used in class reports and archives.")
    parser.add_argument("--exam-date", default=date.today().isoformat(), help="Exam date, usually YYYY-MM-DD.")
    parser.add_argument("--archive-root", type=Path, default=Path("data") / "exams", help="Directory that stores archived exam reports.")
    parser.add_argument("--no-archive", action="store_true", help="Do not copy reports into the exam archive directory.")
    parser.add_argument("--allow-errors", action="store_true", help="Generate trial reports even when blocking validation errors exist.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.make_samples:
        legacy.create_sample_files(args.out_dir)
        print(f"Sample files created in {args.out_dir.resolve()}")
        return 0
    if not args.answer_key and not args.submissions:
        demo_dir = Path("demo")
        legacy.create_sample_files(demo_dir)
        args.answer_key = demo_dir / "answer_key_sample.csv"
        args.submissions = demo_dir / "submissions_sample.csv"
        args.question_bank = demo_dir / "question_bank_sample.csv"
        print("No input files were provided. Running the built-in demo data.")
        print("Use --answer-key and --submissions when you are ready to grade your own files.")
        print()
    if not args.answer_key or not args.submissions:
        parser.error("--answer-key and --submissions are required unless --make-samples is used.")

    result = run_grading(
        answer_key_path=args.answer_key,
        submissions_path=args.submissions,
        question_bank_path=args.question_bank,
        out_dir=args.out_dir,
        exam_name=args.exam_name,
        class_name=args.class_name,
        subject=args.subject,
        exam_date=args.exam_date,
        weak_threshold=args.weak_threshold,
        practice_per_tag=args.practice_per_tag,
        archive_root=args.archive_root,
        no_archive=args.no_archive,
        allow_errors=args.allow_errors,
    )
    print()
    if result["ok"]:
        print("批改完成。")
        print(f"请打开：{result['index']}")
        if result.get("archived_dir"):
            print(f"考试归档已保存到：{result['archived_dir']}")
        return 0
    print("批改已暂停：发现需要先处理的问题。")
    print(f"请打开错误报告：{result['error_report']}")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
