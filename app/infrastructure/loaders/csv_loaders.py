"""CSV loaders matching the legacy answer-key and submissions loaders."""

import csv
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from app.domain.grading.models import (
    AnswerKey,
    DuplicateQuestionIssue,
    QuestionSpec,
    QuestionType,
    Submission,
)
from app.domain.grading.normalize import normalize_answer, parse_question_number
from app.domain.grading.question_types import resolve_question_type


TRUTHY = {"1", "true", "yes", "y", "是", "对", "允许", "partial"}
QUESTION_STATUSES = {
    "normal",
    "cancelled",
    "bonus_all",
    "bonus_if_answered",
    "manual_review",
}

FIELD_ALIASES = {
    "question": ("question", "题号", "number", "q"),
    "answer": ("answer", "答案", "correct", "key"),
    "points": ("points", "score", "分值"),
    "tags": ("tags", "tag", "知识点"),
    "partial": ("partial_credit", "partial", "部分给分"),
    "student_id": ("student_id", "id", "学号", "考号"),
    "name": ("name", "姓名"),
    "bank_id": ("bank_id", "question_id", "id", "题目id"),
    "difficulty": ("difficulty", "level", "难度"),
    "partial_points": (
        "partial_points",
        "partial_score",
        "部分分",
        "漏选分",
    ),
    "answer_aliases": ("answer_aliases", "aliases", "等价答案"),
    "tolerance": ("tolerance", "tol", "误差"),
    "status": ("status", "状态"),
    "question_type": ("question_type", "type", "题型", "题目类型"),
}


def parse_bool(value: object) -> bool:
    return str(value or "").strip().lower() in TRUTHY


def read_csv(path: Path) -> List[Dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} does not contain a header row.")
        return list(reader)


def first_present(
    row: Dict[str, str],
    names: Iterable[str],
    default: str = "",
) -> str:
    folded = {
        key.strip().lower(): value
        for key, value in row.items()
        if key is not None
    }
    for name in names:
        value = folded.get(name.lower())
        if value is not None and str(value).strip():
            return value
    return default


def split_tags(value: str) -> Tuple[str, ...]:
    value = (value or "").replace("，", ";").replace(",", ";").replace("、", ";")
    return tuple(part.strip() for part in value.split(";") if part.strip())


def split_aliases(value: str) -> Tuple[str, ...]:
    value = (value or "").replace("；", ";")
    return tuple(part.strip() for part in value.split(";") if part.strip())


def parse_optional_float(value: object) -> Optional[float]:
    text = str(value or "").strip()
    return float(text) if text else None


def parse_status(value: object) -> str:
    status = str(value or "").strip().lower() or "normal"
    if status not in QUESTION_STATUSES:
        raise ValueError(f"unknown question status: {status}")
    return status


def parse_question_type(value: object, answer_raw: str, answers: FrozenSet[str]) -> str:
    if not str(answer_raw or "").strip() and not str(value or "").strip():
        # Preserve legacy CSV readability.  The canonical precheck rejects the
        # missing expected answer before scoring, so this is not an inference.
        return QuestionType.BLANK.value
    return resolve_question_type(value, answer_raw, answers)


def parse_difficulty(value: object) -> int:
    text = str(value or "").strip().lower()
    if not text:
        return 0
    named = {"easy": 1, "medium": 3, "normal": 3, "hard": 5}
    if text in named:
        return named[text]
    try:
        number = int(float(text))
    except ValueError:
        return 0
    return max(1, min(5, number))


def load_answer_key(path: Path) -> AnswerKey:
    rows = read_csv(Path(path))
    questions: List[QuestionSpec] = []
    seen: Set[int] = set()
    duplicate_questions: List[int] = []
    duplicate_issues: List[DuplicateQuestionIssue] = []
    first_rows: Dict[int, Tuple[int, str, str, str]] = {}
    for index, row in enumerate(rows, start=2):
        number_raw = first_present(row, FIELD_ALIASES["question"])
        answer_raw = first_present(row, FIELD_ALIASES["answer"])
        if not number_raw:
            raise ValueError(f"Answer key row {index}: missing question number.")
        number = int(str(number_raw).strip())
        points_raw = first_present(row, FIELD_ALIASES["points"], "1")
        type_raw = first_present(row, FIELD_ALIASES["question_type"])
        if number in seen:
            duplicate_questions.append(number)
            first = first_rows[number]
            duplicate_issues.append(DuplicateQuestionIssue(
                number, (first[0], index), (first[1], str(answer_raw)),
                (first[2], str(points_raw)), (first[3], str(type_raw)),
                (first[1], first[2], first[3]) != (str(answer_raw), str(points_raw), str(type_raw)),
            ))
            continue
        tags_raw = first_present(row, FIELD_ALIASES["tags"])
        questions.append(
            QuestionSpec(
                number=number,
                answers=normalize_answer(answer_raw),
                points=float(points_raw),
                partial_credit=parse_bool(
                    first_present(row, FIELD_ALIASES["partial"])
                ),
                partial_points=parse_optional_float(
                    first_present(row, FIELD_ALIASES["partial_points"])
                ),
                tags=split_tags(tags_raw),
                source_id=first_present(row, FIELD_ALIASES["bank_id"]).strip(),
                difficulty=parse_difficulty(
                    first_present(row, FIELD_ALIASES["difficulty"])
                ),
                answer_text=str(answer_raw or "").strip(),
                answer_aliases=split_aliases(
                    first_present(row, FIELD_ALIASES["answer_aliases"])
                ),
                tolerance=parse_optional_float(
                    first_present(row, FIELD_ALIASES["tolerance"])
                ),
                status=parse_status(
                    first_present(row, FIELD_ALIASES["status"], "normal")
                ),
                question_type=parse_question_type(type_raw, str(answer_raw or ""), normalize_answer(answer_raw)),
            )
        )
        seen.add(number)
        first_rows[number] = (index, str(answer_raw), str(points_raw), str(type_raw))
    if not questions:
        raise ValueError("Answer key is empty.")
    return AnswerKey(
        tuple(sorted(questions, key=lambda question: question.number)),
        tuple(duplicate_questions),
        tuple(duplicate_issues),
    )


def load_submissions(path: Path, answer_key: AnswerKey) -> List[Submission]:
    rows = read_csv(Path(path))
    valid_questions = set(answer_key.by_number)
    submissions: List[Submission] = []
    for row_number, row in enumerate(rows, start=2):
        student_id = first_present(
            row, FIELD_ALIASES["student_id"], str(row_number - 1)
        ).strip()
        name = first_present(row, FIELD_ALIASES["name"], student_id).strip()
        answers: Dict[int, FrozenSet[str]] = {}
        raw_answers: Dict[int, str] = {}
        extra_questions: List[int] = []
        for header, value in row.items():
            if header is None:
                continue
            number = parse_question_number(header)
            if number in valid_questions:
                answers[number] = normalize_answer(value)
                raw_answers[number] = str(value or "").strip()
            elif number is not None:
                extra_questions.append(number)
        submissions.append(
            Submission(
                student_id=student_id,
                name=name,
                answers=answers,
                raw_answers=raw_answers,
                extra_questions=tuple(sorted(set(extra_questions))),
                row_number=row_number,
            )
        )
    return submissions
