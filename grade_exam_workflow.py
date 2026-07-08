#!/usr/bin/env python3
"""End-to-end class-aware grading workflow.

The workflow prepares class-matched submissions, then delegates scoring to
objective_grader.py without changing the deterministic grading rules.
"""

import argparse
import csv
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import objective_grader
from roster_manager import class_dir, load_roster, match_student, normalize_student_id
from app.workflow import make_run_id, run_grading


DEFAULT_EXAMS_ROOT = PROJECT_ROOT / "data" / "exams"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def safe_exam_part(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError("exam name/date cannot be empty.")
    for char in '<>:"/\\|?*':
        text = text.replace(char, "")
    return text


def exam_dir(out_root: Path, class_name: str, exam_date: str, exam_name: str, run_id: str) -> Path:
    return out_root / safe_exam_part(class_name) / f"{safe_exam_part(exam_date)}_{safe_exam_part(exam_name)}_{run_id}"


def read_csv_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} does not contain a header row.")
        return list(reader.fieldnames), list(reader)


def write_dicts(path: Path, fieldnames: List[str], rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def copy_into_dir(source: Path, target_dir: Path, target_name: str) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / target_name
    if source.resolve() != target.resolve():
        shutil.copy2(str(source), str(target))
    return target


def answer_key_question_headers(answer_key_path: Path) -> List[str]:
    answer_key = objective_grader.load_answer_key(answer_key_path)
    return [f"Q{question.number}" for question in answer_key.questions]


def recognized_question_headers(headers: List[str]) -> List[str]:
    return [header for header in headers if objective_grader.parse_question_number(header) is not None]


def _id_variants(student_id: str) -> List[str]:
    variants = {
        student_id.replace("O", "0").replace("o", "0"),
        student_id.replace("0", "O"),
        student_id.replace("I", "1").replace("l", "1"),
        student_id.replace("1", "I"),
    }
    if len(student_id) > 1:
        variants.add(student_id[:-1])
        variants.add(student_id[1:])
    return [value for value in variants if value and value != student_id]


def suggest_student_match(class_name: str, student_id: str, recognized_name: str = "") -> Dict[str, object]:
    try:
        roster = load_roster(class_name)
    except Exception:
        roster = {}
    if not roster:
        return {"suggested_student_id": "", "suggested_name": "", "confidence": 0}
    for variant in _id_variants(student_id):
        if variant in roster:
            return {"suggested_student_id": variant, "suggested_name": roster[variant], "confidence": 92}
    if recognized_name:
        for roster_id, name in roster.items():
            if str(name).strip() == str(recognized_name).strip():
                return {"suggested_student_id": roster_id, "suggested_name": name, "confidence": 88}
    best_id = ""
    best_name = ""
    best_score = 0.0
    for roster_id, name in roster.items():
        score = SequenceMatcher(None, student_id, roster_id).ratio()
        if recognized_name:
            score = max(score, SequenceMatcher(None, recognized_name, name).ratio() * 0.92)
        if score > best_score:
            best_score = score
            best_id = roster_id
            best_name = name
    confidence = int(round(best_score * 100))
    if confidence < 70:
        return {"suggested_student_id": "", "suggested_name": "", "confidence": confidence}
    return {"suggested_student_id": best_id, "suggested_name": best_name, "confidence": confidence}


def validate_preflight(class_name: str, answer_key_path: Path, recognized_path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    try:
        current_class_dir = class_dir(class_name)
    except FileNotFoundError as exc:
        rows.append({"severity": "error", "scope": "class", "item": class_name, "message": str(exc)})
        current_class_dir = None
    if current_class_dir is not None and not (current_class_dir / "roster.csv").exists():
        rows.append({"severity": "error", "scope": "class", "item": "roster.csv", "message": "该班级还没有学生名单，请先导入。"})
    if not recognized_path.exists():
        rows.append({"severity": "error", "scope": "input", "item": str(recognized_path), "message": "找不到识别结果文件 recognized_submissions.csv"})
    if not answer_key_path.exists():
        rows.append({"severity": "error", "scope": "input", "item": str(answer_key_path), "message": "找不到答案文件 answer_key.csv"})
    return rows


def convert_recognized_submissions(
    class_name: str,
    recognized_path: Path,
    submissions_path: Path,
    unmatched_path: Path,
    answer_key_path: Path,
) -> Dict[str, object]:
    headers, rows = read_csv_rows(recognized_path)
    if "recognized_student_id" not in headers:
        raise ValueError("recognized_submissions.csv must contain recognized_student_id column.")

    question_headers = recognized_question_headers(headers)
    expected_headers = answer_key_question_headers(answer_key_path)
    expected_numbers = {objective_grader.parse_question_number(header) for header in expected_headers}
    actual_numbers = {objective_grader.parse_question_number(header) for header in question_headers}
    validation_rows: List[Dict[str, object]] = []
    if expected_numbers != actual_numbers:
        validation_rows.append(
            {
                "severity": "warning",
                "scope": "recognized_submissions",
                "item": "question_columns",
                "message": f"answer columns {sorted(actual_numbers)} do not match answer key {sorted(expected_numbers)}",
            }
        )

    output_rows: List[Dict[str, object]] = []
    unmatched_rows: List[Dict[str, object]] = []
    matched_count = 0
    duplicate_counter: Counter = Counter()

    for row_number, row in enumerate(rows, start=2):
        raw_id = row.get("recognized_student_id", "")
        recognized_name = row.get("recognized_name", "") or row.get("name", "")
        normalized_id, id_warnings = normalize_student_id(raw_id)
        result = match_student(class_name, normalized_id)
        message = str(result["message"])
        if id_warnings:
            message = f"{message}; {'; '.join(id_warnings)}" if message else "; ".join(id_warnings)
        name = str(result["name"]) if result["matched"] else f"UNMATCHED_{normalized_id}"
        if result["matched"]:
            matched_count += 1
        else:
            suggestion = suggest_student_match(class_name, normalized_id, recognized_name)
            unmatched_rows.append(
                {
                    "recognized_student_id": normalized_id,
                    "row_number": row_number,
                    "message": message,
                    "suggested_student_id": suggestion["suggested_student_id"],
                    "suggested_name": suggestion["suggested_name"],
                    "confidence": suggestion["confidence"],
                    "action": "pending",
                }
            )
            validation_rows.append({"severity": "warning", "scope": "student_match", "item": normalized_id, "message": message})

        duplicate_counter[normalized_id] += 1
        output = {"student_id": normalized_id, "name": name}
        for header in expected_headers:
            source_header = next((actual for actual in question_headers if objective_grader.parse_question_number(actual) == objective_grader.parse_question_number(header)), header)
            output[header] = row.get(source_header, "")
        output_rows.append(output)

    for student_id, count in duplicate_counter.items():
        if student_id and count > 1:
            validation_rows.append({"severity": "warning", "scope": "submissions", "item": student_id, "message": "duplicate student_id in submissions.csv"})

    write_dicts(submissions_path, ["student_id", "name"] + expected_headers, output_rows)
    write_dicts(
        unmatched_path,
        ["recognized_student_id", "row_number", "message", "suggested_student_id", "suggested_name", "confidence", "action"],
        unmatched_rows,
    )
    return {
        "submission_count": len(output_rows),
        "matched_count": matched_count,
        "unmatched_count": len(unmatched_rows),
        "validation_rows": validation_rows,
    }


def merge_validation_report(report_path: Path, extra_rows: List[Dict[str, object]]) -> None:
    fieldnames = ["severity", "scope", "item", "message"]
    rows: List[Dict[str, object]] = []
    if report_path.exists():
        with report_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    rows.extend(extra_rows)
    write_dicts(report_path, fieldnames, rows)


def write_exam_metadata(path: Path, data: Dict[str, object]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_grader(
    answer_key_path: Path,
    submissions_path: Path,
    out_dir: Path,
    exam_name: str,
    class_name: str,
    subject: str,
    exam_date: str,
) -> None:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "objective_grader.py"),
        "--answer-key",
        str(answer_key_path),
        "--submissions",
        str(submissions_path),
        "--out-dir",
        str(out_dir),
        "--exam-name",
        exam_name,
        "--class-name",
        class_name,
        "--subject",
        subject,
        "--exam-date",
        exam_date,
        "--no-archive",
    ]
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), text=True, capture_output=True)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"批改程序运行失败，退出代码 {completed.returncode}。{message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run class-aware objective grading workflow.")
    parser.add_argument("--class-name", required=True)
    parser.add_argument("--exam-name", required=True)
    parser.add_argument("--exam-date", required=True)
    parser.add_argument("--subject", default="数学")
    parser.add_argument("--answer-key", required=True, type=Path)
    parser.add_argument("--recognized-submissions", required=True, type=Path)
    parser.add_argument("--out-root", default=DEFAULT_EXAMS_ROOT, type=Path)
    return parser


def run_grader(
    answer_key_path: Path,
    submissions_path: Path,
    out_dir: Path,
    exam_name: str,
    class_name: str,
    subject: str,
    exam_date: str,
    run_id: str,
    extra_validation_rows: Optional[List[Dict[str, object]]] = None,
) -> None:
    result = run_grading(
        answer_key_path=answer_key_path,
        submissions_path=submissions_path,
        out_dir=out_dir,
        exam_name=exam_name,
        class_name=class_name,
        subject=subject,
        exam_date=exam_date,
        no_archive=True,
        run_id=run_id,
        extra_validation_rows=extra_validation_rows or [],
        source_files={
            "answer_key": "answer_key.csv",
            "recognized_submissions": "recognized_submissions.csv",
            "submissions": "submissions.csv",
        },
    )
    if not result["ok"]:
        raise RuntimeError(f"批改暂停：请查看 {result.get('error_report', out_dir / 'error_report.html')}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    class_name = args.class_name
    answer_key_source = args.answer_key
    recognized_source = args.recognized_submissions
    preflight_rows = validate_preflight(class_name, answer_key_source, recognized_source)
    if any(row["severity"] == "error" for row in preflight_rows):
        for row in preflight_rows:
            print(row["message"], file=sys.stderr)
        return 1

    roster = load_roster(class_name)
    run_id = make_run_id()
    target_dir = exam_dir(args.out_root, class_name, args.exam_date, args.exam_name, run_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    answer_key_path = copy_into_dir(answer_key_source, target_dir, "answer_key.csv")
    recognized_path = copy_into_dir(recognized_source, target_dir, "recognized_submissions.csv")
    submissions_path = target_dir / "submissions.csv"
    unmatched_path = target_dir / "unmatched_students.csv"

    conversion = convert_recognized_submissions(class_name, recognized_path, submissions_path, unmatched_path, answer_key_path)
    run_grader(
        answer_key_path,
        submissions_path,
        target_dir,
        args.exam_name,
        class_name,
        args.subject,
        args.exam_date,
        run_id,
        extra_validation_rows=preflight_rows + list(conversion["validation_rows"]),
    )

    validation_report_path = target_dir / "validation_report.csv"
    merge_validation_report(validation_report_path, preflight_rows + list(conversion["validation_rows"]))
    metadata = {
        "exam_name": args.exam_name,
        "class_name": class_name,
        "subject": args.subject,
        "exam_date": args.exam_date,
        "run_id": run_id,
        "student_count_in_roster": len(roster),
        "submission_count": conversion["submission_count"],
        "matched_count": conversion["matched_count"],
        "unmatched_count": conversion["unmatched_count"],
        "answer_key_path": "answer_key.csv",
        "submissions_path": "submissions.csv",
        "source_files": {
            "answer_key": "answer_key.csv",
            "recognized_submissions": "recognized_submissions.csv",
            "submissions": "submissions.csv",
        },
        "created_at": now_iso(),
    }
    write_exam_metadata(target_dir / "exam_metadata.json", metadata)
    print()
    print("批改完成。")
    print()
    print("请打开：")
    print(target_dir / "index.html")
    print()
    print("如果需要：")
    print(f"普通版报告：{target_dir / 'simple_report.html'}")
    print(f"高级学情分析：{target_dir / 'advanced_dashboard.html'}")
    print(f"简单成绩表：{target_dir / 'simple_score_report.xlsx'}")
    print()
    print("数据底稿已保存到：")
    print(f"{target_dir}/")
    print()
    print("考试归档已保存到：")
    print(f"{target_dir}/")
    print(f"匹配成功 {conversion['matched_count']} 人，未匹配 {conversion['unmatched_count']} 人。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
