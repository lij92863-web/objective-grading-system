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

from app.workflow import run_grading
from app.infrastructure.samples.sample_files import create_sample_files
from app.compat.objective_grader_compat import (
    COMPAT_EXPORTS,
    export_compat_symbols,
)

globals().update(export_compat_symbols())


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
        create_sample_files(args.out_dir)
        print(f"Sample files created in {args.out_dir.resolve()}")
        return 0
    if not args.answer_key and not args.submissions:
        demo_dir = Path("demo")
        create_sample_files(demo_dir)
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
