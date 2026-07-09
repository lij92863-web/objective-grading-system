"""CSV loaders matching the legacy answer-key and submissions loaders."""

import csv
import dataclasses
import re
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple


OPTION_RE = re.compile(r"[A-Z0-9]+")
QUESTION_RE = re.compile(r"^(?:q|question|题)?\s*0*(\d+)$", re.IGNORECASE)
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
}


@dataclasses.dataclass(frozen=True)
class QuestionSpec:
    number: int
    answers: FrozenSet[str]
    points: float = 1.0
    partial_credit: bool = False
    partial_points: Optional[float] = None
    tags: Tuple[str, ...] = ()
    source_id: str = ""
    difficulty: int = 0
    answer_text: str = ""
    answer_aliases: Tuple[str, ...] = ()
    tolerance: Optional[float] = None
    status: str = "normal"


@dataclasses.dataclass(frozen=True)
class AnswerKey:
    questions: Tuple[QuestionSpec, ...]
    duplicate_questions: Tuple[int, ...] = ()

    @property
    def total_points(self) -> float:
        return sum(
            question.points
            for question in self.questions
            if question.status not in {"cancelled", "manual_review"}
        )

    @property
    def by_number(self) -> Dict[int, QuestionSpec]:
        return {question.number: question for question in self.questions}


@dataclasses.dataclass(frozen=True)
class Submission:
    student_id: str
    name: str
    answers: Dict[int, FrozenSet[str]]
    raw_answers: Dict[int, str]
    extra_questions: Tuple[int, ...]
    row_number: int


def normalize_answer(value: object) -> FrozenSet[str]:
    if value is None:
        return frozenset()
    text = str(value).strip().upper()
    if not text:
        return frozenset()
    text = (
        text.replace("，", ",")
        .replace("；", ";")
        .replace("、", ",")
        .replace("|", ",")
        .replace("/", ",")
    )
    tokens = OPTION_RE.findall(text)
    if len(tokens) == 1 and len(tokens[0]) > 1 and tokens[0].isalpha():
        tokens = list(tokens[0])
    return frozenset(token for token in tokens if token)


def parse_bool(value: object) -> bool:
    return str(value or "").strip().lower() in TRUTHY


def parse_question_number(header: str) -> Optional[int]:
    match = QUESTION_RE.match(str(header).strip())
    return int(match.group(1)) if match else None


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
    return status if status in QUESTION_STATUSES else status


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
    for index, row in enumerate(rows, start=2):
        number_raw = first_present(row, FIELD_ALIASES["question"])
        answer_raw = first_present(row, FIELD_ALIASES["answer"])
        if not number_raw:
            raise ValueError(f"Answer key row {index}: missing question number.")
        number = int(str(number_raw).strip())
        if number in seen:
            duplicate_questions.append(number)
            continue
        tags_raw = first_present(row, FIELD_ALIASES["tags"])
        questions.append(
            QuestionSpec(
                number=number,
                answers=normalize_answer(answer_raw),
                points=float(first_present(row, FIELD_ALIASES["points"], "1")),
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
            )
        )
        seen.add(number)
    if not questions:
        raise ValueError("Answer key is empty.")
    return AnswerKey(
        tuple(sorted(questions, key=lambda question: question.number)),
        tuple(duplicate_questions),
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
