#!/usr/bin/env python3
"""Recognize, validate, confirm, and export exam structure manifests.

The recognizer is an input-layer module. It never grades submissions and never
feeds unconfirmed AI/OCR output directly into objective_grader.py.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


QUESTION_TYPES = {
    "single_choice": "单选题",
    "multiple_choice": "多选题",
    "blank": "填空题",
    "true_false": "判断题",
    "solution": "解答题",
    "proof": "证明题",
    "unknown": "未知题型",
}
AUTO_GRADABLE_TYPES = {"single_choice", "multiple_choice", "true_false"}
OBJECTIVE_TYPES = {"single_choice", "multiple_choice", "blank", "true_false"}
PAPER_SUFFIXES = {".jpg", ".jpeg", ".png", ".pdf", ".docx"}
ANSWER_SUFFIXES = {".jpg", ".jpeg", ".png", ".pdf", ".docx", ".xlsx", ".csv"}
ANSWER_KEY_FIELDS = ["question", "answer", "points", "partial_credit", "partial_points", "tags", "difficulty"]


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def read_json(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ANSWER_KEY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in ANSWER_KEY_FIELDS})


MANIFEST_REVIEW_FIELDS = [
    "question",
    "type",
    "display_type",
    "answer",
    "points",
    "partial_credit",
    "tags",
    "difficulty",
    "auto_gradable",
    "confidence",
    "warnings",
]


def parse_bool(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "是", "对"}


def write_manifest_review_csv(path: Path, manifest: Dict[str, object]) -> None:
    rows = []
    for item in manifest.get("questions", []):
        qtype = str(item.get("type") or "unknown")
        rows.append(
            {
                "question": item.get("question", ""),
                "type": qtype,
                "display_type": item.get("display_type", QUESTION_TYPES.get(qtype, qtype)),
                "answer": item.get("answer", ""),
                "points": item.get("points", ""),
                "partial_credit": "true" if qtype == "multiple_choice" else "false",
                "tags": ";".join(str(tag) for tag in item.get("tags", [])),
                "difficulty": item.get("difficulty", ""),
                "auto_gradable": "true" if item.get("auto_gradable") else "false",
                "confidence": item.get("confidence", ""),
                "warnings": ";".join(str(message) for message in item.get("warnings", [])),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def review_csv_to_questions(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        questions = []
        for row in reader:
            qtype = str(row.get("type") or "unknown").strip()
            if qtype not in QUESTION_TYPES:
                qtype = "unknown"
            tags = [part.strip() for part in str(row.get("tags") or "").replace(",", ";").split(";") if part.strip()]
            warnings = [part.strip() for part in str(row.get("warnings") or "").split(";") if part.strip()]
            questions.append(
                {
                    "question": row.get("question", ""),
                    "type": qtype,
                    "display_type": row.get("display_type") or QUESTION_TYPES.get(qtype, qtype),
                    "answer": row.get("answer", ""),
                    "points": row.get("points", ""),
                    "partial_credit": row.get("partial_credit", ""),
                    "tags": tags,
                    "difficulty": row.get("difficulty", ""),
                    "auto_gradable": parse_bool(row.get("auto_gradable")),
                    "confidence": row.get("confidence", ""),
                    "warnings": warnings,
                    "source": "teacher_review_csv",
                }
            )
    return questions


def normalize_answer(value: object) -> str:
    text = str(value or "").strip().upper()
    text = text.replace("，", ",").replace("；", ";").replace("、", ",").replace(" ", "")
    if not text:
        return ""
    tokens = re.findall(r"[A-Z0-9]+", text)
    if len(tokens) == 1 and tokens[0].isalpha() and len(tokens[0]) > 1:
        return "".join(sorted(tokens[0]))
    return "".join(tokens)


def clamp_difficulty(value: object) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return 0
    return number if 0 <= number <= 5 else 0


def normalize_question(question: Dict[str, object]) -> Dict[str, object]:
    qtype = str(question.get("type") or "unknown").strip()
    if qtype not in QUESTION_TYPES:
        qtype = "unknown"
    points = question.get("points", 0)
    try:
        points = float(points)
    except (TypeError, ValueError):
        points = 0
    if points.is_integer():
        points = int(points)

    answer = normalize_answer(question.get("answer", ""))
    auto_gradable = bool(question.get("auto_gradable", False))
    if qtype in AUTO_GRADABLE_TYPES:
        auto_gradable = True
    elif qtype in {"solution", "proof", "unknown"}:
        auto_gradable = False
    elif qtype == "blank":
        auto_gradable = bool(auto_gradable and answer)

    tags = question.get("tags", [])
    if isinstance(tags, str):
        tags = [part.strip() for part in re.split(r"[;,；，、]", tags) if part.strip()]
    if not isinstance(tags, list):
        tags = []

    confidence = question.get("confidence", 0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0

    normalized = dict(question)
    normalized.update(
        {
            "type": qtype,
            "display_type": QUESTION_TYPES[qtype],
            "points": points,
            "answer": answer,
            "auto_gradable": auto_gradable,
            "tags": tags,
            "difficulty": clamp_difficulty(question.get("difficulty", 0)),
            "confidence": confidence,
            "source": question.get("source") or "ai_recognition",
            "warnings": list(question.get("warnings") or []),
        }
    )
    return normalized


def is_auto_gradable_type(qtype: str) -> bool:
    return qtype in AUTO_GRADABLE_TYPES


def validate_exam_manifest(manifest: Dict[str, object]) -> Tuple[Dict[str, object], List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []

    if not manifest.get("exam_name"):
        warnings.append("缺少考试名称，请老师确认。")
    if not manifest.get("subject"):
        warnings.append("缺少科目，请老师确认。")
    if not manifest.get("exam_date"):
        warnings.append("缺少考试日期，请老师确认。")

    questions = [normalize_question(item) for item in manifest.get("questions", []) if isinstance(item, dict)]
    question_count = int(manifest.get("question_count") or 0)
    if question_count != len(questions):
        warnings.append(f"系统识别的题目数量是{question_count}题，但题目明细中有{len(questions)}题，请老师确认。")

    total_score = manifest.get("total_score", 0)
    try:
        total_score_number = float(total_score)
    except (TypeError, ValueError):
        total_score_number = 0
        warnings.append("系统没有识别到有效总分，请老师确认。")
    points_sum = sum(float(item.get("points") or 0) for item in questions)
    if abs(total_score_number - points_sum) > 0.0001:
        warnings.append(f"系统识别的总分是{format_number(total_score_number)}分，但各题分值相加为{format_number(points_sum)}分，请检查分值是否识别错误。")

    numbers: List[int] = []
    seen = set()
    for item in questions:
        number = item.get("question")
        try:
            number_int = int(number)
            item["question"] = number_int
            numbers.append(number_int)
        except (TypeError, ValueError):
            warnings.append("存在题号缺失或无法识别的题目，请老师确认。")
            continue
        if number_int in seen:
            warnings.append(f"第{number_int}题重复出现，请老师确认。")
        seen.add(number_int)

        qtype = str(item.get("type") or "")
        if not qtype:
            warnings.append(f"第{number_int}题缺少题型，请老师确认。")
        if qtype == "unknown":
            warnings.append(f"第{number_int}题题型未知，请老师确认。")
        if not item.get("points"):
            warnings.append(f"第{number_int}题分值为0或未识别到分值，请老师确认。")
        if item.get("difficulty", 0) < 0 or item.get("difficulty", 0) > 5:
            warnings.append(f"第{number_int}题难度不在0-5之间，请老师确认。")
        if item.get("confidence", 0) < 0 or item.get("confidence", 0) > 1:
            warnings.append(f"第{number_int}题识别置信度不在0-1之间，请老师确认。")

        if item.get("auto_gradable") and not item.get("answer"):
            message = f"第{number_int}题是客观题，但没有标准答案，不能生成正式 answer_key.csv。"
            warnings.append(message)
            errors.append(message)
        if qtype in OBJECTIVE_TYPES and is_auto_gradable_type(qtype) and not item.get("answer"):
            warnings.append(f"第{number_int}题是客观题，但没有识别到标准答案，请检查答案文件或手动补充。")

    if numbers:
        expected = set(range(min(numbers), max(numbers) + 1))
        missing = sorted(expected - set(numbers))
        if missing:
            warnings.append(f"题号不连续，缺少第{','.join(str(item) for item in missing)}题，请老师确认。")

    auto_count = sum(1 for item in questions if item.get("auto_gradable"))
    manual_count = len(questions) - auto_count
    manifest["questions"] = sorted(questions, key=lambda item: int(item.get("question") or 0))
    manifest["question_count"] = len(questions)
    manifest["auto_gradable_count"] = auto_count
    manifest["manual_grade_count"] = manual_count
    manifest["total_score"] = int(total_score_number) if total_score_number.is_integer() else total_score_number
    merged_warnings = []
    for message in list(manifest.get("warnings") or []) + warnings:
        if message not in merged_warnings:
            merged_warnings.append(message)
    manifest["warnings"] = merged_warnings
    manifest["needs_teacher_review"] = True
    return manifest, merged_warnings, errors


def format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def build_recognition_report(manifest: Dict[str, object], paper: Path, answer: Path, warnings: List[str]) -> Dict[str, object]:
    questions = manifest.get("questions", [])
    confidences = [float(item.get("confidence") or 0) for item in questions]
    confidence_average = sum(confidences) / len(confidences) if confidences else 0
    return {
        "input_files": {"paper": str(paper), "answer": str(answer)},
        "recognized_question_count": manifest.get("question_count", 0),
        "recognized_auto_gradable_count": manifest.get("auto_gradable_count", 0),
        "recognized_manual_grade_count": manifest.get("manual_grade_count", 0),
        "total_score": manifest.get("total_score", 0),
        "confidence_average": round(confidence_average, 2),
        "warnings": warnings,
        "needs_teacher_review": True,
    }


def make_mock_manifest(exam_name: str, class_name: str, subject: str, exam_date: str) -> Dict[str, object]:
    answers = {
        1: "A",
        2: "B",
        3: "C",
        4: "D",
        5: "A",
        6: "B",
        7: "C",
        8: "D",
        9: "AC",
        10: "BD",
        11: "2",
        12: "4",
    }
    tags = {
        1: ["集合运算"],
        2: ["函数概念"],
        3: ["三角函数"],
        4: ["数列基础"],
        5: ["不等式"],
        6: ["解析几何"],
        7: ["概率统计"],
        8: ["向量"],
        9: ["函数性质"],
        10: ["导数基础"],
        11: ["计算能力"],
        12: ["方程求解"],
        13: ["导数综合"],
        14: ["函数综合"],
    }
    questions: List[Dict[str, object]] = []
    for number in range(1, 9):
        questions.append(mock_question(number, "single_choice", 5, answers[number], tags[number], 1 + (number % 3), 0.95))
    for number in range(9, 11):
        questions.append(mock_question(number, "multiple_choice", 5, answers[number], tags[number], 3, 0.88))
    for number in range(11, 13):
        questions.append(mock_question(number, "blank", 5, answers[number], tags[number], 2, 0.84))
    for number in range(13, 15):
        questions.append(mock_question(number, "solution", 15, "", tags[number], 4, 0.76, ["解答题暂不自动批改"]))

    return {
        "exam_name": exam_name,
        "class_name": class_name,
        "subject": subject,
        "exam_date": exam_date,
        "total_score": 90,
        "question_count": 14,
        "auto_gradable_count": 12,
        "manual_grade_count": 2,
        "questions": questions,
        "warnings": ["第13-14题为解答题，暂不自动批改"],
        "needs_teacher_review": True,
        "created_at": now_iso(),
        "recognition_mode": "mock",
    }


def mock_question(
    number: int,
    qtype: str,
    points: int,
    answer: str,
    tags: List[str],
    difficulty: int,
    confidence: float,
    warnings: Optional[List[str]] = None,
) -> Dict[str, object]:
    auto_gradable = qtype in AUTO_GRADABLE_TYPES or (qtype == "blank" and bool(answer))
    return {
        "question": number,
        "type": qtype,
        "display_type": QUESTION_TYPES[qtype],
        "points": points,
        "answer": answer,
        "auto_gradable": auto_gradable,
        "tags": tags,
        "difficulty": difficulty,
        "confidence": confidence,
        "source": "mock_recognition",
        "warnings": warnings or [],
    }


def recognize_exam(args: argparse.Namespace) -> int:
    paper = Path(args.paper)
    answer = Path(args.answer)
    if paper.suffix.lower() not in PAPER_SUFFIXES:
        print("试卷文件格式暂不支持，请使用 jpg、jpeg、png、pdf 或 docx。", file=sys.stderr)
        return 1
    if answer.suffix.lower() not in ANSWER_SUFFIXES:
        print("标准答案文件格式暂不支持，请使用 jpg、jpeg、png、pdf、docx、xlsx 或 csv。", file=sys.stderr)
        return 1
    if not args.mock:
        if not paper.exists():
            print(f"没有找到试卷文件：{paper}。当前未接入真实 OCR/AI，测试文件流可加 --mock。", file=sys.stderr)
            return 1
        if not answer.exists():
            print(f"没有找到标准答案文件：{answer}。当前未接入真实 OCR/AI，测试文件流可加 --mock。", file=sys.stderr)
            return 1
        print("当前还没有接入真实 OCR/AI，请先使用 --mock 跑通文件流。", file=sys.stderr)
        return 1

    manifest = make_mock_manifest(args.exam_name, args.class_name, args.subject, args.exam_date)
    manifest, warnings, _errors = validate_exam_manifest(manifest)
    out_dir = Path(args.out_dir)
    write_json(out_dir / "exam_manifest.json", manifest)
    write_manifest_review_csv(out_dir / "manifest_review.csv", manifest)
    write_json(out_dir / "recognition_report.json", build_recognition_report(manifest, paper, answer, warnings))
    print(f"已生成考试结构：{(out_dir / 'exam_manifest.json').resolve()}")
    print(f"已生成识别报告：{(out_dir / 'recognition_report.json').resolve()}")
    print("请老师检查 exam_manifest.json，确认后再生成 answer_key.csv。")
    return 0


def confirm_manifest(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    if manifest_path.name == "confirmed_exam_manifest.json":
        print("这个文件已经是 confirmed_exam_manifest.json，无需重复确认。")
        return 0
    if not manifest_path.exists():
        print(f"没有找到考试结构文件：{manifest_path}", file=sys.stderr)
        return 1
    manifest = read_json(manifest_path)
    manifest, warnings, _errors = validate_exam_manifest(manifest)
    if warnings:
        print("确认前请注意以下提示：")
        for message in warnings:
            print(f"- {message}")
    manifest["confirmed_at"] = now_iso()
    manifest["confirmation_method"] = "cli_copy_after_teacher_review"
    target = manifest_path.parent / "confirmed_exam_manifest.json"
    write_json(target, manifest)
    report_path = manifest_path.parent / "recognition_report.json"
    if report_path.exists():
        report = read_json(report_path)
        report["warnings"] = warnings
        report["needs_teacher_review"] = True
        write_json(report_path, report)
    print(f"已生成确认版考试结构：{target.resolve()}")
    return 0


def confirm_review(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    review_path = Path(args.review)
    if not manifest_path.exists():
        print(f"没有找到考试结构文件：{manifest_path}", file=sys.stderr)
        return 1
    if not review_path.exists():
        print(f"没有找到教师确认表：{review_path}", file=sys.stderr)
        return 1
    manifest = read_json(manifest_path)
    manifest["questions"] = review_csv_to_questions(review_path)
    manifest, warnings, errors = validate_exam_manifest(manifest)
    if warnings:
        print("确认表中仍有需要注意的信息：")
        for message in warnings:
            print(f"- {message}")
    if errors:
        print("确认表中还有不能生成正式答案表的问题：", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1
    manifest["confirmed_at"] = now_iso()
    manifest["confirmation_method"] = "manifest_review_csv"
    target = manifest_path.parent / "confirmed_exam_manifest.json"
    write_json(target, manifest)
    print(f"已生成确认版考试结构：{target.resolve()}")
    return 0


def build_answer_key(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    if manifest_path.name != "confirmed_exam_manifest.json":
        print("不能直接使用 exam_manifest.json 生成正式 answer_key.csv。请先运行 confirm 生成 confirmed_exam_manifest.json。", file=sys.stderr)
        return 1
    if not manifest_path.exists():
        print(f"没有找到确认版考试结构文件：{manifest_path}", file=sys.stderr)
        return 1
    manifest = read_json(manifest_path)
    manifest, warnings, errors = validate_exam_manifest(manifest)
    score_mismatch = [message for message in warnings if "总分" in message and "各题分值" in message]
    if score_mismatch:
        print("系统识别的总分与各题分值之和不一致，请老师确认。", file=sys.stderr)
        for message in score_mismatch:
            print(f"- {message}", file=sys.stderr)
        return 1
    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1

    rows: List[Dict[str, object]] = []
    for item in manifest.get("questions", []):
        if not item.get("auto_gradable"):
            continue
        answer = normalize_answer(item.get("answer"))
        if not answer:
            print(f"第{item.get('question')}题是客观题，但没有标准答案，不能生成正式 answer_key.csv。", file=sys.stderr)
            return 1
        qtype = item.get("type")
        rows.append(
            {
                "question": item.get("question"),
                "answer": answer,
                "points": item.get("points", 0),
                "partial_credit": "true" if qtype == "multiple_choice" else "false",
                "partial_points": "",
                "tags": ";".join(str(tag) for tag in item.get("tags", [])),
                "difficulty": clamp_difficulty(item.get("difficulty", 0)),
            }
        )

    write_csv(Path(args.out), rows)
    print(f"已生成 answer_key.csv：{Path(args.out).resolve()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recognize and confirm exam structures before objective grading.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    recognize = subparsers.add_parser("recognize", help="Recognize exam structure and write exam_manifest.json.")
    recognize.add_argument("--paper", required=True)
    recognize.add_argument("--answer", required=True)
    recognize.add_argument("--exam-name", required=True)
    recognize.add_argument("--class-name", required=True)
    recognize.add_argument("--subject", default="数学")
    recognize.add_argument("--exam-date", required=True)
    recognize.add_argument("--out-dir", required=True)
    recognize.add_argument("--mock", action="store_true", help="Use mock recognition to test the file flow.")

    confirm = subparsers.add_parser("confirm", help="Confirm an editable exam_manifest.json.")
    confirm.add_argument("--manifest", required=True)

    confirm_review_parser = subparsers.add_parser("confirm-review", help="Confirm manifest_review.csv and write confirmed_exam_manifest.json.")
    confirm_review_parser.add_argument("--manifest", required=True)
    confirm_review_parser.add_argument("--review", required=True)

    build_key = subparsers.add_parser("build-answer-key", help="Build answer_key.csv from confirmed_exam_manifest.json.")
    build_key.add_argument("--manifest", required=True)
    build_key.add_argument("--out", required=True)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "recognize":
        return recognize_exam(args)
    if args.command == "confirm":
        return confirm_manifest(args)
    if args.command == "confirm-review":
        return confirm_review(args)
    if args.command == "build-answer-key":
        return build_answer_key(args)
    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except json.JSONDecodeError as exc:
        print(f"JSON 文件格式不正确，请检查逗号、引号和括号是否完整：{exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"处理失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
