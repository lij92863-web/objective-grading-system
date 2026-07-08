#!/usr/bin/env python3
"""CSV-based objective question grader.

The code stays dependency-free on purpose: it is easier to run on a teacher's
computer, easier to audit, and easier to extend later with OCR or LLM input.
"""

import argparse
import csv
import dataclasses
import json
import re
import shutil
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple


OPTION_RE = re.compile(r"[A-Z0-9]+")
QUESTION_RE = re.compile(r"^(?:q|question|\u9898)?\s*0*(\d+)$", re.IGNORECASE)
TRUTHY = {"1", "true", "yes", "y", "\u662f", "\u5bf9", "\u5141\u8bb8", "partial"}
CHOICE_OPTIONS = set("ABCDEFGH")
EPSILON = 1e-9

FIELD_ALIASES = {
    "question": ("question", "\u9898\u53f7", "number", "q"),
    "answer": ("answer", "\u7b54\u6848", "correct", "key"),
    "points": ("points", "score", "\u5206\u503c"),
    "tags": ("tags", "tag", "\u77e5\u8bc6\u70b9"),
    "partial": ("partial_credit", "partial", "\u90e8\u5206\u7ed9\u5206"),
    "student_id": ("student_id", "id", "\u5b66\u53f7", "\u8003\u53f7"),
    "name": ("name", "\u59d3\u540d"),
    "bank_id": ("bank_id", "question_id", "id", "\u9898\u76eeid"),
    "stem": ("stem", "question_text", "content", "\u9898\u5e72"),
    "difficulty": ("difficulty", "level", "\u96be\u5ea6"),
    "partial_points": ("partial_points", "partial_score", "\u90e8\u5206\u5206", "\u6f0f\u9009\u5206"),
    "answer_aliases": ("answer_aliases", "aliases", "\u7b49\u4ef7\u7b54\u6848"),
    "tolerance": ("tolerance", "tol", "\u8bef\u5dee"),
    "status": ("status", "\u72b6\u6001"),
}

QUESTION_STATUSES = {"normal", "cancelled", "bonus_all", "bonus_if_answered", "manual_review"}


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
        return sum(question.points for question in self.questions if question.status not in {"cancelled", "manual_review"})

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


@dataclasses.dataclass(frozen=True)
class QuestionResult:
    number: int
    expected: FrozenSet[str]
    actual: FrozenSet[str]
    raw_actual: str
    score: float
    max_score: float
    status: str


@dataclasses.dataclass(frozen=True)
class StudentResult:
    student_id: str
    name: str
    score: float
    max_score: float
    percent: float
    correct_count: int
    wrong_or_partial_count: int
    blank_count: int
    invalid_count: int
    details: Tuple[QuestionResult, ...]


@dataclasses.dataclass(frozen=True)
class BankQuestion:
    question_id: str
    stem: str
    answer: str
    tags: Tuple[str, ...]
    difficulty: int = 0


@dataclasses.dataclass(frozen=True)
class KnowledgeProfile:
    student_id: str
    name: str
    tag: str
    score: float
    max_score: float
    mastery: float
    question_count: int
    weak: bool
    mastery_level: str


@dataclasses.dataclass(frozen=True)
class ExamMeta:
    exam_name: str
    class_name: str
    subject: str
    exam_date: str


def normalize_answer(value: object) -> FrozenSet[str]:
    """Normalize AC, A,C, a c, and full-width separators into option tokens."""
    if value is None:
        return frozenset()
    text = str(value).strip().upper()
    if not text:
        return frozenset()
    text = (
        text.replace("\uff0c", ",")
        .replace("\uff1b", ";")
        .replace("\u3001", ",")
        .replace("|", ",")
        .replace("/", ",")
    )
    tokens = OPTION_RE.findall(text)
    if len(tokens) == 1 and len(tokens[0]) > 1 and tokens[0].isalpha():
        tokens = list(tokens[0])
    return frozenset(token for token in tokens if token)


def format_answer(answer: FrozenSet[str]) -> str:
    return "".join(sorted(answer))


def parse_bool(value: object) -> bool:
    return str(value or "").strip().lower() in TRUTHY


def parse_question_number(header: str) -> Optional[int]:
    match = QUESTION_RE.match(str(header).strip())
    return int(match.group(1)) if match else None


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} does not contain a header row.")
        return list(reader)


def first_present(row: Dict[str, str], names: Iterable[str], default: str = "") -> str:
    folded = {key.strip().lower(): value for key, value in row.items() if key is not None}
    for name in names:
        value = folded.get(name.lower())
        if value is not None and str(value).strip():
            return value
    return default


def split_tags(value: str) -> Tuple[str, ...]:
    value = (value or "").replace("\uff0c", ";").replace(",", ";").replace("\u3001", ";")
    return tuple(part.strip() for part in value.split(";") if part.strip())


def split_aliases(value: str) -> Tuple[str, ...]:
    value = (value or "").replace("\uff1b", ";")
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
    rows = read_csv(path)
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
        answers = normalize_answer(answer_raw)
        status = parse_status(first_present(row, FIELD_ALIASES["status"], default="normal"))
        points = float(first_present(row, FIELD_ALIASES["points"], default="1"))
        tags_raw = first_present(row, FIELD_ALIASES["tags"])
        questions.append(
            QuestionSpec(
                number=number,
                answers=answers,
                points=points,
                partial_credit=parse_bool(first_present(row, FIELD_ALIASES["partial"])),
                partial_points=parse_optional_float(first_present(row, FIELD_ALIASES["partial_points"])),
                tags=split_tags(tags_raw),
                source_id=first_present(row, FIELD_ALIASES["bank_id"]).strip(),
                difficulty=parse_difficulty(first_present(row, FIELD_ALIASES["difficulty"])),
                answer_text=str(answer_raw or "").strip(),
                answer_aliases=split_aliases(first_present(row, FIELD_ALIASES["answer_aliases"])),
                tolerance=parse_optional_float(first_present(row, FIELD_ALIASES["tolerance"])),
                status=status,
            )
        )
        seen.add(number)
    if not questions:
        raise ValueError("Answer key is empty.")
    return AnswerKey(tuple(sorted(questions, key=lambda question: question.number)), tuple(duplicate_questions))


def load_question_bank(path: Path) -> List[BankQuestion]:
    rows = read_csv(path)
    questions: List[BankQuestion] = []
    seen: Set[str] = set()
    for index, row in enumerate(rows, start=2):
        question_id = first_present(row, FIELD_ALIASES["bank_id"]).strip()
        if not question_id:
            raise ValueError(f"Question bank row {index}: missing question id.")
        if question_id in seen:
            raise ValueError(f"Question bank row {index}: duplicate question id {question_id}.")
        questions.append(
            BankQuestion(
                question_id=question_id,
                stem=first_present(row, FIELD_ALIASES["stem"]).strip(),
                answer=first_present(row, FIELD_ALIASES["answer"]).strip(),
                tags=split_tags(first_present(row, FIELD_ALIASES["tags"])),
                difficulty=parse_difficulty(first_present(row, FIELD_ALIASES["difficulty"])),
            )
        )
        seen.add(question_id)
    return questions


def load_submissions(path: Path, answer_key: AnswerKey) -> List[Submission]:
    rows = read_csv(path)
    valid_questions = set(answer_key.by_number)
    submissions: List[Submission] = []
    for row_number, row in enumerate(rows, start=2):
        student_id = first_present(row, FIELD_ALIASES["student_id"], default=str(row_number - 1)).strip()
        name = first_present(row, FIELD_ALIASES["name"], default=student_id).strip()
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


def allowed_options(spec: QuestionSpec) -> Set[str]:
    return CHOICE_OPTIONS | set(spec.answers)


def is_choice_answer(answer: FrozenSet[str]) -> bool:
    return bool(answer) and all(token in CHOICE_OPTIONS for token in answer)


def is_choice_like_answer(spec: QuestionSpec) -> bool:
    return is_choice_answer(spec.answers) and any(char.isalpha() for char in spec.answer_text.upper())


def format_expected_answer(spec: QuestionSpec) -> str:
    return spec.answer_text if (spec.answer_aliases or spec.tolerance is not None) else format_answer(spec.answers)


def normalize_text_answer(value: object) -> str:
    return str(value or "").strip().replace("\uff0c", ",").replace("\uff1b", ";").replace("\u3000", " ").lower()


def numeric_value(value: object) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    fraction = re.fullmatch(r"\\frac\{([-+]?\d+(?:\.\d+)?)\}\{([-+]?\d+(?:\.\d+)?)\}", text)
    if fraction:
        denominator = float(fraction.group(2))
        return float(fraction.group(1)) / denominator if denominator else None
    simple_fraction = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)/([-+]?\d+(?:\.\d+)?)", text)
    if simple_fraction:
        denominator = float(simple_fraction.group(2))
        return float(simple_fraction.group(1)) / denominator if denominator else None
    try:
        return float(text)
    except ValueError:
        return None


def matches_text_answer(spec: QuestionSpec, raw_actual: str) -> bool:
    actual_text = normalize_text_answer(raw_actual)
    if not actual_text:
        return False
    accepted = [spec.answer_text] + list(spec.answer_aliases)
    for answer in accepted:
        if actual_text == normalize_text_answer(answer):
            return True
    if spec.tolerance is not None:
        actual_number = numeric_value(raw_actual)
        expected_numbers = [numeric_value(answer) for answer in accepted]
        if actual_number is not None:
            for expected_number in expected_numbers:
                if expected_number is not None and abs(actual_number - expected_number) <= spec.tolerance + EPSILON:
                    return True
    return False


def score_answer(spec: QuestionSpec, actual: FrozenSet[str], raw_actual: str = "") -> Tuple[float, str]:
    """Score one answer with deterministic school-test rules."""
    if spec.status == "cancelled":
        return 0.0, "cancelled"
    if spec.status == "manual_review":
        return 0.0, "manual_review"
    if spec.status == "bonus_all":
        return spec.points, "bonus"
    if spec.status == "bonus_if_answered":
        return (spec.points, "bonus") if actual or raw_actual.strip() else (0.0, "blank")
    if normalize_text_answer(raw_actual) in {"unrecognized", "__unrecognized__", "识别失败"}:
        return 0.0, "unrecognized"
    if not actual and not raw_actual.strip():
        return 0.0, "blank"
    if ((spec.answer_aliases or spec.tolerance is not None) or not is_choice_answer(spec.answers)) and matches_text_answer(spec, raw_actual):
        return spec.points, "correct"
    if actual and actual == spec.answers:
        return spec.points, "correct"
    if is_choice_answer(spec.answers) and not actual <= allowed_options(spec):
        return 0.0, "invalid"
    if len(spec.answers) == 1:
        return 0.0, "wrong"
    if spec.partial_credit and len(spec.answers) > 1:
        wrong_selected = actual - spec.answers
        right_selected = actual & spec.answers
        if wrong_selected:
            return 0.0, "wrong"
        if right_selected:
            return round(spec.points * len(right_selected) / len(spec.answers), 4), "partial"
    return 0.0, "wrong"


def grade_submission(answer_key: AnswerKey, submission: Submission) -> StudentResult:
    details: List[QuestionResult] = []
    status_counts: Counter = Counter()
    score = 0.0
    for spec in answer_key.questions:
        actual = submission.answers.get(spec.number, frozenset())
        raw_actual = submission.raw_answers.get(spec.number, "")
        question_score, status = score_answer(spec, actual, raw_actual)
        max_score = 0.0 if spec.status in {"cancelled", "manual_review"} else spec.points
        status_counts[status] += 1
        score += question_score
        details.append(
            QuestionResult(
                number=spec.number,
                expected=spec.answers,
                actual=actual,
                raw_actual=raw_actual,
                score=question_score,
                max_score=max_score,
                status=status,
            )
        )
    max_score = answer_key.total_points
    return StudentResult(
        student_id=submission.student_id,
        name=submission.name,
        score=round(score, 4),
        max_score=max_score,
        percent=round(score / max_score * 100, 2) if max_score else 0.0,
        correct_count=status_counts["correct"],
        wrong_or_partial_count=status_counts["wrong"] + status_counts["partial"],
        blank_count=status_counts["blank"],
        invalid_count=status_counts["invalid"],
        details=tuple(details),
    )


def grade_all(answer_key: AnswerKey, submissions: Iterable[Submission]) -> List[StudentResult]:
    return [grade_submission(answer_key, submission) for submission in submissions]


def competition_ranks(results: List[StudentResult]) -> List[int]:
    sorted_results = sorted(enumerate(results), key=lambda item: (-item[1].score, item[0]))
    ranks = [0 for _result in results]
    previous_score: Optional[float] = None
    current_rank = 0
    for position, (_index, result) in enumerate(sorted_results, start=1):
        if previous_score is None or result.score != previous_score:
            current_rank = position
        ranks[_index] = current_rank
        previous_score = result.score
    return ranks


def write_summary(path: Path, results: List[StudentResult]) -> None:
    ranks = competition_ranks(results)
    rows = [
        {
            "student_id": result.student_id,
            "name": result.name,
            "rank": ranks[index],
            "score": result.score,
            "max_score": result.max_score,
            "percent": result.percent,
            "correct_count": result.correct_count,
            "wrong_or_partial_count": result.wrong_or_partial_count,
            "blank_count": result.blank_count,
            "invalid_count": result.invalid_count,
        }
        for index, result in enumerate(results)
    ]
    write_dicts(path, rows)


def write_detail(path: Path, answer_key: AnswerKey, results: List[StudentResult]) -> None:
    question_specs = answer_key.by_number
    rows = []
    for result in results:
        for detail in result.details:
            spec = question_specs[detail.number]
            rows.append(
                {
                    "student_id": result.student_id,
                    "name": result.name,
                    "question": detail.number,
                    "question_id": spec.source_id,
                    "question_status": spec.status,
                    "difficulty": spec.difficulty,
                    "tags": ";".join(spec.tags),
                    "expected": format_expected_answer(spec),
                    "actual": format_answer(detail.actual),
                    "raw_actual": detail.raw_actual,
                    "score": detail.score,
                    "max_score": detail.max_score,
                    "status": detail.status,
                }
            )
    write_dicts(path, rows)


def write_item_analysis(path: Path, answer_key: AnswerKey, results: List[StudentResult]) -> None:
    by_question: Dict[int, List[QuestionResult]] = defaultdict(list)
    for result in results:
        for detail in result.details:
            by_question[detail.number].append(detail)
    rows = []
    for spec in answer_key.questions:
        details = by_question[spec.number]
        total = len(details) or 1
        correct = sum(1 for detail in details if detail.status == "correct")
        partial = sum(1 for detail in details if detail.status == "partial")
        wrong = sum(1 for detail in details if detail.status == "wrong")
        blank = sum(1 for detail in details if detail.status == "blank")
        invalid = sum(1 for detail in details if detail.status == "invalid")
        distribution = Counter(format_answer(detail.actual) or "(blank)" for detail in details)
        rows.append(
            {
                "question": spec.number,
                "question_id": spec.source_id,
                "question_status": spec.status,
                "difficulty": spec.difficulty,
                "tags": ";".join(spec.tags),
                "answer": format_expected_answer(spec),
                "points": spec.points,
                "accuracy": round(correct / total * 100, 2),
                "blank_rate": round(blank / total * 100, 2),
                "wrong_rate": round(wrong / total * 100, 2),
                "partial_rate": round(partial / total * 100, 2),
                "invalid_rate": round(invalid / total * 100, 2),
                "option_distribution": json.dumps(dict(distribution), ensure_ascii=False),
            }
        )
    write_dicts(path, rows)


def build_knowledge_profiles(
    answer_key: AnswerKey,
    results: List[StudentResult],
    weak_threshold: float = 70.0,
) -> List[KnowledgeProfile]:
    question_specs = answer_key.by_number
    profiles: List[KnowledgeProfile] = []
    for result in results:
        tag_scores: Dict[str, float] = defaultdict(float)
        tag_max_scores: Dict[str, float] = defaultdict(float)
        tag_counts: Dict[str, int] = defaultdict(int)
        for detail in result.details:
            if detail.max_score <= 0:
                continue
            spec = question_specs[detail.number]
            tags = spec.tags or ("untagged",)
            for tag in tags:
                tag_scores[tag] += detail.score
                tag_max_scores[tag] += detail.max_score
                tag_counts[tag] += 1
        for tag in sorted(tag_max_scores):
            max_score = tag_max_scores[tag]
            mastery = round(tag_scores[tag] / max_score * 100, 2) if max_score else 0.0
            profiles.append(
                KnowledgeProfile(
                    student_id=result.student_id,
                    name=result.name,
                    tag=tag,
                    score=round(tag_scores[tag], 4),
                    max_score=round(max_score, 4),
                    mastery=mastery,
                    question_count=tag_counts[tag],
                    weak=mastery < weak_threshold,
                    mastery_level=mastery_level(mastery),
                )
            )
    return profiles


def mastery_level(mastery: float) -> str:
    if mastery < 40:
        return "严重薄弱"
    if mastery < 60:
        return "明显薄弱"
    if mastery < 80:
        return "基本掌握"
    return "掌握较好"


def write_knowledge_profiles(path: Path, profiles: List[KnowledgeProfile]) -> None:
    rows = [
        {
            "student_id": profile.student_id,
            "name": profile.name,
            "tag": profile.tag,
            "score": profile.score,
            "max_score": profile.max_score,
            "mastery": profile.mastery,
            "mastery_level": profile.mastery_level,
            "question_count": profile.question_count,
            "weak": "yes" if profile.weak else "no",
        }
        for profile in profiles
    ]
    write_dicts(path, rows)


def build_correct_question_ids(answer_key: AnswerKey, results: List[StudentResult]) -> Dict[str, Set[str]]:
    question_specs = answer_key.by_number
    correct_ids: Dict[str, Set[str]] = defaultdict(set)
    for result in results:
        for detail in result.details:
            if detail.max_score <= 0:
                continue
            spec = question_specs[detail.number]
            if spec.source_id and detail.status == "correct":
                correct_ids[result.student_id].add(spec.source_id)
    return correct_ids


def build_target_difficulties(answer_key: AnswerKey, results: List[StudentResult]) -> Dict[Tuple[str, str], int]:
    question_specs = answer_key.by_number
    misses_by_tag: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    for result in results:
        for detail in result.details:
            if detail.max_score <= 0:
                continue
            if detail.status == "correct":
                continue
            spec = question_specs[detail.number]
            if not spec.difficulty:
                continue
            for tag in spec.tags or ("untagged",):
                misses_by_tag[(result.student_id, tag)].append(spec.difficulty)

    targets: Dict[Tuple[str, str], int] = {}
    for key, difficulties in misses_by_tag.items():
        targets[key] = int(round(statistics.mean(difficulties)))
    return targets


def difficulty_rank(question_difficulty: int, target_difficulty: int) -> Tuple[int, int, int]:
    if not target_difficulty or not question_difficulty:
        return (9, 9, question_difficulty or 9)
    if question_difficulty == target_difficulty:
        return (0, 0, question_difficulty)
    if question_difficulty == target_difficulty - 1:
        return (1, 0, question_difficulty)
    return (2, abs(question_difficulty - target_difficulty), question_difficulty)


def recommend_practice(
    profiles: List[KnowledgeProfile],
    question_bank: List[BankQuestion],
    per_tag: int,
    already_correct: Optional[Dict[str, Set[str]]] = None,
    target_difficulties: Optional[Dict[Tuple[str, str], int]] = None,
) -> List[Dict[str, object]]:
    already_correct = already_correct or {}
    target_difficulties = target_difficulties or {}
    bank_by_tag: Dict[str, List[BankQuestion]] = defaultdict(list)
    for question in question_bank:
        for tag in question.tags:
            bank_by_tag[tag].append(question)

    rows: List[Dict[str, object]] = []
    weak_profiles = sorted(profiles, key=lambda profile: (profile.student_id, profile.mastery, profile.tag))
    for profile in weak_profiles:
        if not profile.weak:
            continue
        target_difficulty = target_difficulties.get((profile.student_id, profile.tag), 0)
        selected = 0
        candidates = sorted(
            bank_by_tag.get(profile.tag, []),
            key=lambda question: difficulty_rank(question.difficulty, target_difficulty),
        )
        for question in candidates:
            if question.question_id in already_correct.get(profile.student_id, set()):
                continue
            rows.append(
                {
                    "student_id": profile.student_id,
                    "name": profile.name,
                    "weak_tag": profile.tag,
                    "mastery": profile.mastery,
                    "question_id": question.question_id,
                    "target_difficulty": target_difficulty,
                    "difficulty": question.difficulty,
                    "difficulty_delta": abs(question.difficulty - target_difficulty) if target_difficulty and question.difficulty else "",
                    "stem": question.stem,
                    "answer": question.answer,
                    "tags": ";".join(question.tags),
                }
            )
            selected += 1
            if selected >= per_tag:
                break
    return rows


def write_practice_recommendations(path: Path, rows: List[Dict[str, object]]) -> None:
    if rows:
        write_dicts(path, rows)
        return
    write_dicts_with_fields(
        path,
        [
            "student_id",
            "name",
            "weak_tag",
            "mastery",
            "question_id",
            "target_difficulty",
            "difficulty",
            "difficulty_delta",
            "stem",
            "answer",
            "tags",
        ],
        [],
    )


def build_class_report(
    answer_key: AnswerKey,
    results: List[StudentResult],
    profiles: List[KnowledgeProfile],
    meta: ExamMeta,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    scores = [result.score for result in results]
    max_score = answer_key.total_points
    rows.append({"section": "exam", "metric": "exam_name", "value": meta.exam_name, "extra": ""})
    rows.append({"section": "exam", "metric": "class_name", "value": meta.class_name, "extra": ""})
    rows.append({"section": "exam", "metric": "subject", "value": meta.subject, "extra": ""})
    rows.append({"section": "exam", "metric": "exam_date", "value": meta.exam_date, "extra": ""})
    rows.append({"section": "score", "metric": "student_count", "value": len(results), "extra": ""})
    rows.append({"section": "score", "metric": "max_score", "value": round(max_score, 4), "extra": ""})
    if scores:
        rows.append({"section": "score", "metric": "average", "value": round(statistics.mean(scores), 2), "extra": ""})
        rows.append({"section": "score", "metric": "median", "value": round(statistics.median(scores), 2), "extra": ""})
        rows.append({"section": "score", "metric": "highest", "value": round(max(scores), 2), "extra": ""})
        rows.append({"section": "score", "metric": "lowest", "value": round(min(scores), 2), "extra": ""})
        pass_count = sum(1 for result in results if result.percent >= 60)
        excellent_count = sum(1 for result in results if result.percent >= 90)
        low_count = sum(1 for result in results if result.percent < 60)
        rows.append({"section": "score", "metric": "pass_rate", "value": round(pass_count / len(results) * 100, 2), "extra": "percent >= 60"})
        rows.append({"section": "score", "metric": "excellent_rate", "value": round(excellent_count / len(results) * 100, 2), "extra": "percent >= 90"})
        rows.append({"section": "score", "metric": "low_score_rate", "value": round(low_count / len(results) * 100, 2), "extra": "percent < 60"})
        bands = [
            ("90%-100%", lambda percent: percent >= 90),
            ("80%-89%", lambda percent: 80 <= percent < 90),
            ("70%-79%", lambda percent: 70 <= percent < 80),
            ("60%-69%", lambda percent: 60 <= percent < 70),
            ("below_60%", lambda percent: percent < 60),
        ]
        for label, predicate in bands:
            count = sum(1 for result in results if predicate(result.percent))
            rows.append({"section": "score_band", "metric": label, "value": count, "extra": f"{round(count / len(results) * 100, 2)}%"})

    tag_profiles: Dict[str, List[KnowledgeProfile]] = defaultdict(list)
    for profile in profiles:
        tag_profiles[profile.tag].append(profile)
    for tag in sorted(tag_profiles):
        tag_items = tag_profiles[tag]
        average_mastery = statistics.mean(profile.mastery for profile in tag_items)
        weak_count = sum(1 for profile in tag_items if profile.weak)
        rows.append(
            {
                "section": "knowledge",
                "metric": tag,
                "value": round(average_mastery, 2),
                "extra": f"weak_students={weak_count}",
            }
        )

    question_specs = answer_key.by_number
    for spec in answer_key.questions:
        details = [detail for result in results for detail in result.details if detail.number == spec.number]
        if not details:
            continue
        correct = sum(1 for detail in details if detail.status == "correct")
        partial = sum(1 for detail in details if detail.status == "partial")
        blank = sum(1 for detail in details if detail.status == "blank")
        wrong = sum(1 for detail in details if detail.status == "wrong")
        accuracy = round(correct / len(details) * 100, 2)
        distribution = Counter(format_answer(detail.actual) or "(blank)" for detail in details)
        rows.append(
            {
                "section": "item",
                "metric": f"Q{spec.number}",
                "value": accuracy,
                "extra": (
                    f"tags={';'.join(question_specs[spec.number].tags)};"
                    f"blank_rate={round(blank / len(details) * 100, 2)};"
                    f"wrong_rate={round(wrong / len(details) * 100, 2)};"
                    f"partial_rate={round(partial / len(details) * 100, 2)};"
                    f"option_distribution={json.dumps(dict(distribution), ensure_ascii=False)}"
                ),
            }
        )
    return rows


def write_class_report(path: Path, rows: List[Dict[str, object]]) -> None:
    write_dicts_with_fields(path, ["section", "metric", "value", "extra"], rows)


def build_validation_report(
    answer_key: AnswerKey,
    submissions: List[Submission],
    results: List[StudentResult],
    profiles: List[KnowledgeProfile],
    question_bank: Optional[List[BankQuestion]] = None,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    bank_ids = set(question.question_id for question in question_bank or [])
    bank_tags = set(tag for question in question_bank or [] for tag in question.tags)

    student_counts = Counter(submission.student_id for submission in submissions)
    for student_id, count in sorted(student_counts.items()):
        if count > 1:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "submission",
                    "item": student_id,
                    "message": f"duplicate student_id appears {count} times",
                }
            )
    answer_key_numbers = set(answer_key.by_number)
    submitted_numbers = set()
    for submission in submissions:
        submitted_numbers.update(submission.answers)
        for number in submission.extra_questions:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "submission",
                    "item": f"{submission.student_id}:Q{number}",
                    "message": "submissions.csv contains a question that is not in answer_key.csv",
                }
            )
    for number in sorted(answer_key_numbers - submitted_numbers):
        rows.append(
            {
                "severity": "info",
                "scope": "submission",
                "item": f"Q{number}",
                "message": "answer_key.csv contains a question that no submission answered",
            }
        )

    for number in answer_key.duplicate_questions:
        rows.append(
            {
                "severity": "error",
                "scope": "answer_key",
                "item": f"Q{number}",
                "message": "duplicate question number in answer_key.csv; later duplicate row was ignored",
            }
        )

    for spec in answer_key.questions:
        if spec.status not in QUESTION_STATUSES:
            rows.append(
                {
                    "severity": "error",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": f"invalid status {spec.status}; expected one of {', '.join(sorted(QUESTION_STATUSES))}",
                }
            )
        if spec.points <= 0:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "question points should be positive",
                }
            )
        if spec.status == "cancelled":
            rows.append(
                {
                    "severity": "info",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "cancelled question is excluded from total score",
                }
            )
        if spec.status == "manual_review":
            rows.append(
                {
                    "severity": "info",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "manual_review question is not automatically graded and is excluded from total score",
                }
            )
        if spec.status in {"bonus_all", "bonus_if_answered"}:
            rows.append(
                {
                    "severity": "info",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": f"{spec.status} question uses bonus scoring",
                }
            )
        if spec.status == "normal" and not spec.answers:
            rows.append(
                {
                    "severity": "error",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "objective question is missing a correct answer",
                }
            )
        if is_choice_like_answer(spec) and len(spec.answers) > 1 and not spec.partial_credit:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "multiple-answer question should set partial_credit=true for proportional scoring",
                }
            )
        if spec.partial_credit and is_choice_like_answer(spec) and len(spec.answers) < 2 and spec.status == "normal":
            rows.append(
                {
                    "severity": "info",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "partial_credit=true has no effect when the answer has only one option",
                }
            )
        if not spec.tags:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "question has no knowledge point tags",
                }
            )
        if not spec.difficulty:
            rows.append(
                {
                    "severity": "info",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "question has no 1-5 difficulty value",
                }
            )
        if spec.partial_points is not None and spec.partial_points > spec.points:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": "partial_points is greater than full points",
                }
            )
        if question_bank is not None and spec.source_id and spec.source_id not in bank_ids:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "answer_key",
                    "item": f"Q{spec.number}",
                    "message": f"question_id {spec.source_id} is not found in question bank",
                }
            )

    if question_bank is not None:
        for question in question_bank:
            if not question.tags:
                rows.append(
                    {
                        "severity": "warning",
                        "scope": "question_bank",
                        "item": question.question_id,
                        "message": "bank question has no tags",
                    }
                )
            if not question.stem:
                rows.append(
                    {
                        "severity": "info",
                        "scope": "question_bank",
                        "item": question.question_id,
                        "message": "bank question has empty stem",
                    }
                )
            if not question.difficulty:
                rows.append(
                    {
                        "severity": "info",
                        "scope": "question_bank",
                        "item": question.question_id,
                        "message": "bank question has no 1-5 difficulty value",
                    }
                )

    weak_tags = set(profile.tag for profile in profiles if profile.weak)
    for tag in sorted(weak_tags):
        if question_bank is not None and tag not in bank_tags:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "practice",
                    "item": tag,
                    "message": "weak tag has no matching question in question bank",
                }
            )

    for result in results:
        if result.invalid_count:
            rows.append(
                {
                    "severity": "warning",
                    "scope": "grading",
                    "item": result.student_id,
                    "message": f"student has {result.invalid_count} invalid answers",
                }
            )

    if not rows:
        rows.append({"severity": "ok", "scope": "all", "item": "", "message": "no validation issues found"})
    return rows


def write_validation_report(path: Path, rows: List[Dict[str, object]]) -> None:
    write_dicts_with_fields(path, ["severity", "scope", "item", "message"], rows)


def write_student_report(path: Path, results: List[StudentResult], profiles: List[KnowledgeProfile]) -> None:
    ranks = competition_ranks(results)
    weak_tags_by_student: Dict[str, List[str]] = defaultdict(list)
    for profile in profiles:
        if profile.weak:
            weak_tags_by_student[profile.student_id].append(profile.tag)
    rows = []
    for index, result in enumerate(results):
        by_status: Dict[str, List[str]] = defaultdict(list)
        for detail in result.details:
            by_status[detail.status].append(str(detail.number))
        rows.append(
            {
                "student_id": result.student_id,
                "name": result.name,
                "score": result.score,
                "max_score": result.max_score,
                "percent": result.percent,
                "rank": ranks[index],
                "weak_tags": ";".join(sorted(weak_tags_by_student.get(result.student_id, []))),
                "wrong_questions": ";".join(by_status["wrong"]),
                "partial_questions": ";".join(by_status["partial"]),
                "blank_questions": ";".join(by_status["blank"]),
                "invalid_questions": ";".join(by_status["invalid"]),
            }
        )
    write_dicts_with_fields(
        path,
        [
            "student_id",
            "name",
            "score",
            "max_score",
            "percent",
            "rank",
            "weak_tags",
            "wrong_questions",
            "partial_questions",
            "blank_questions",
            "invalid_questions",
        ],
        rows,
    )


def write_dicts(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_dicts_with_fields(path: Path, fieldnames: List[str], rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_for_workbook(path: Path) -> List[List[str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [list(row) for row in csv.reader(handle)]


def excel_column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def worksheet_xml(rows: List[List[str]]) -> str:
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{excel_column_name(col_index)}{row_index}"
            text = escape(str(value))
            cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


def xml_attr(value: str) -> str:
    return escape(value, {'"': "&quot;"})


def write_xlsx(path: Path, sheets: List[Tuple[str, List[List[str]]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_sheets = [(sheet_name[:31], rows or [["empty"]]) for sheet_name, rows in sheets]
    workbook_sheets = []
    workbook_rels = []
    content_overrides = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for index, (sheet_name, _rows) in enumerate(safe_sheets, start=1):
        workbook_sheets.append(f'<sheet name="{xml_attr(sheet_name)}" sheetId="{index}" r:id="rId{index}"/>')
        workbook_rels.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        )
        content_overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + "".join(content_overrides)
        + "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(workbook_sheets)}</sheets>'
        "</workbook>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(workbook_rels)
        + "</Relationships>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        for index, (_sheet_name, rows) in enumerate(safe_sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", worksheet_xml(rows))


def write_workbook(path: Path, report_files: List[Tuple[str, Path]]) -> None:
    sheets = [(sheet_name, read_csv_for_workbook(csv_path)) for sheet_name, csv_path in report_files]
    write_xlsx(path, sheets)


def html_escape(value: object) -> str:
    return escape(str(value), {'"': "&quot;", "'": "&#x27;"})


def pct(value: float) -> str:
    return f"{value:.2f}%"


def basic_stats(results: List[StudentResult]) -> Dict[str, object]:
    scores = [result.score for result in results]
    if not scores:
        return {"average": 0, "highest": 0, "lowest": 0, "pass_rate": 0, "excellent_rate": 0}
    return {
        "average": round(statistics.mean(scores), 2),
        "highest": round(max(scores), 2),
        "lowest": round(min(scores), 2),
        "pass_rate": round(sum(1 for result in results if result.percent >= 60) / len(results) * 100, 2),
        "excellent_rate": round(sum(1 for result in results if result.percent >= 90) / len(results) * 100, 2),
    }


def student_status_map(result: StudentResult) -> Dict[str, List[str]]:
    by_status: Dict[str, List[str]] = defaultdict(list)
    for detail in result.details:
        by_status[detail.status].append(str(detail.number))
    return by_status


def simple_score_rows(results: List[StudentResult]) -> List[Dict[str, object]]:
    ranks = competition_ranks(results)
    rows = []
    for index, result in enumerate(results):
        by_status = student_status_map(result)
        remarks = []
        if result.percent >= 90:
            remarks.append("优秀")
        elif result.percent < 60:
            remarks.append("未及格")
        if by_status["blank"]:
            remarks.append("有空白")
        if by_status["invalid"] or by_status["unrecognized"]:
            remarks.append("有异常答案")
        rows.append(
            {
                "rank": ranks[index],
                "student_id": result.student_id,
                "name": result.name,
                "score": result.score,
                "max_score": result.max_score,
                "percent": result.percent,
                "correct_count": result.correct_count,
                "wrong_or_partial_count": result.wrong_or_partial_count,
                "blank_count": result.blank_count,
                "invalid_count": result.invalid_count,
                "wrong_questions": ";".join(by_status["wrong"] + by_status["invalid"]),
                "blank_questions": ";".join(by_status["blank"]),
                "remark": "；".join(remarks),
            }
        )
    return rows


def item_stats(answer_key: AnswerKey, results: List[StudentResult]) -> List[Dict[str, object]]:
    rows = []
    for spec in answer_key.questions:
        details = [detail for result in results for detail in result.details if detail.number == spec.number]
        total = len(details) or 1
        correct = sum(1 for detail in details if detail.status in {"correct", "bonus"})
        partial = sum(1 for detail in details if detail.status == "partial")
        blank = sum(1 for detail in details if detail.status == "blank")
        invalid = sum(1 for detail in details if detail.status == "invalid")
        wrong = sum(1 for detail in details if detail.status in {"wrong", "invalid", "unrecognized"})
        distribution = Counter(format_answer(detail.actual) or "(blank)" for detail in details)
        rows.append(
            {
                "question": spec.number,
                "tags": ";".join(spec.tags),
                "answer": format_expected_answer(spec),
                "accuracy": round(correct / total * 100, 2),
                "blank_rate": round(blank / total * 100, 2),
                "invalid_rate": round(invalid / total * 100, 2),
                "wrong_rate": round(wrong / total * 100, 2),
                "partial_rate": round(partial / total * 100, 2),
                "mistake_count": wrong + partial,
                "distribution": dict(distribution),
            }
        )
    return rows


def score_bands(results: List[StudentResult]) -> List[Tuple[str, int]]:
    bands = [
        ("90%-100%", lambda percent: percent >= 90),
        ("80%-89%", lambda percent: 80 <= percent < 90),
        ("70%-79%", lambda percent: 70 <= percent < 80),
        ("60%-69%", lambda percent: 60 <= percent < 70),
        ("60%以下", lambda percent: percent < 60),
    ]
    return [(label, sum(1 for result in results if predicate(result.percent))) for label, predicate in bands]


def write_simple_score_workbook(path: Path, rows: List[Dict[str, object]]) -> None:
    fields = [
        "rank",
        "student_id",
        "name",
        "score",
        "max_score",
        "percent",
        "correct_count",
        "wrong_or_partial_count",
        "blank_count",
        "invalid_count",
        "wrong_questions",
        "blank_questions",
        "remark",
    ]
    sheet_rows = [fields] + [[str(row.get(field, "")) for field in fields] for row in rows]
    write_xlsx(path, [("scores", sheet_rows)])


def render_table(headers: List[str], rows: List[List[object]]) -> str:
    header_html = "".join(f"<th>{html_escape(header)}</th>" for header in headers)
    row_html = []
    for row in rows:
        row_html.append("<tr>" + "".join(f"<td>{html_escape(cell)}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{header_html}</tr></thead><tbody>{''.join(row_html)}</tbody></table>"


def bar(label: str, value: float, max_value: float = 100.0) -> str:
    width = 0 if max_value <= 0 else min(100, max(0, value / max_value * 100))
    return (
        '<div class="bar-row">'
        f'<span>{html_escape(label)}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{width:.2f}%"></div></div>'
        f'<strong>{html_escape(value)}</strong>'
        '</div>'
    )


def report_css() -> str:
    return """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;margin:0;background:#f6f7f9;color:#20242a}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:28px;margin:0 0 8px} h2{font-size:18px;margin:28px 0 12px}
.muted{color:#667085}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stat,.panel{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px}
.stat b{display:block;font-size:24px;margin-top:6px}.actions{margin:18px 0}
a.button{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;padding:10px 14px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}
th,td{border-bottom:1px solid #edf0f3;padding:8px 10px;text-align:left;font-size:14px}th{background:#f1f5f9}
.bar-row{display:grid;grid-template-columns:90px 1fr 64px;gap:10px;align-items:center;margin:8px 0}
.bar-track{height:14px;background:#e5e7eb;border-radius:999px;overflow:hidden}.bar-fill{height:100%;background:#2563eb}
.warn{background:#fff7ed;border-color:#fed7aa}.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){main{padding:16px}.two{grid-template-columns:1fr}th,td{font-size:12px;padding:6px}.bar-row{grid-template-columns:70px 1fr 52px}}
"""


def write_simple_report(path: Path, meta: ExamMeta, answer_key: AnswerKey, results: List[StudentResult], simple_rows: List[Dict[str, object]], item_rows: List[Dict[str, object]]) -> None:
    stats = basic_stats(results)
    top_wrong = sorted(item_rows, key=lambda row: (-float(row["mistake_count"]), row["question"]))[:5]
    score_table = render_table(
        ["rank", "student_id", "name", "score", "max_score", "percent", "correct_count", "wrong_or_partial_count", "blank_count", "wrong_questions"],
        [
            [
                row["rank"],
                row["student_id"],
                row["name"],
                row["score"],
                row["max_score"],
                row["percent"],
                row["correct_count"],
                row["wrong_or_partial_count"],
                row["blank_count"],
                row["wrong_questions"],
            ]
            for row in simple_rows
        ],
    )
    item_table = render_table(
        ["题号", "正确率", "空白率"],
        [[f"Q{row['question']}", pct(float(row["accuracy"])), pct(float(row["blank_rate"]))] for row in item_rows],
    )
    top_table = render_table(
        ["题号", "错误/部分得分人数", "正确率", "知识点"],
        [[f"Q{row['question']}", row["mistake_count"], pct(float(row["accuracy"])), row["tags"]] for row in top_wrong],
    )
    bars = "".join(bar(f"Q{row['question']}", float(row["accuracy"])) for row in item_rows)
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>普通版报告 - {html_escape(meta.exam_name)}</title><style>{report_css()}</style></head>
<body><main>
<h1>普通版报告</h1><p class="muted">{html_escape(meta.exam_name)} · {html_escape(meta.class_name or "未填写班级")} · {html_escape(meta.exam_date)}</p>
<div class="actions"><a class="button" href="simple_score_report.xlsx">导出简单 Excel 成绩表</a></div>
<section class="grid">
<div class="stat">参考人数<b>{len(results)}</b></div>
<div class="stat">平均分<b>{stats['average']}</b></div>
<div class="stat">最高分<b>{stats['highest']}</b></div>
<div class="stat">最低分<b>{stats['lowest']}</b></div>
<div class="stat">及格率<b>{pct(float(stats['pass_rate']))}</b></div>
<div class="stat">优秀率<b>{pct(float(stats['excellent_rate']))}</b></div>
</section>
<h2>学生成绩表</h2>{score_table}
<section class="two"><div><h2>每题正确率</h2><div class="panel">{bars}</div></div><div><h2>每题正确率表</h2>{item_table}</div></section>
<h2>错得最多的题 Top 5</h2>{top_table}
</main></body></html>"""
    path.write_text(html, encoding="utf-8")


def percent(value: object) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def get_rate_class(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number < 40:
        return "danger"
    if number < 60:
        return "warning"
    if number < 80:
        return "normal"
    return "good"


def build_score_distribution(results: List[StudentResult]) -> List[Dict[str, object]]:
    return [{"label": label, "value": count, "class": "danger" if label == "60%以下" else "normal"} for label, count in score_bands(results)]


def build_question_accuracy_items(item_analysis_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    items = []
    for row in item_analysis_rows:
        accuracy = float(row.get("accuracy", 0))
        items.append({"label": f"Q{row.get('question')}", "value": accuracy, "display": percent(accuracy), "class": get_rate_class(accuracy)})
    return items


def main_wrong_answer(row: Dict[str, object]) -> str:
    distribution = row.get("distribution", {})
    if not isinstance(distribution, dict):
        return ""
    answer = str(row.get("answer", ""))
    candidates = []
    for option, count in distribution.items():
        option_text = str(option)
        if option_text in {"(blank)", "", answer}:
            continue
        candidates.append((option_text, int(count)))
    if not candidates:
        return ""
    option, count = max(candidates, key=lambda item: item[1])
    return f"{option}（{count}人）"


def build_weak_items(item_analysis_rows: List[Dict[str, object]], top_n: int = 5) -> List[Dict[str, object]]:
    sorted_rows = sorted(item_analysis_rows, key=lambda row: (float(row.get("accuracy", 0)), int(row.get("question", 0))))
    items = []
    for row in sorted_rows[:top_n]:
        accuracy = float(row.get("accuracy", 0))
        if accuracy < 40:
            level = "重点讲评"
        elif accuracy < 60:
            level = "课堂订正"
        else:
            level = "适当回顾"
        items.append(
            {
                "question": row.get("question", ""),
                "accuracy": accuracy,
                "blank_rate": float(row.get("blank_rate", 0)),
                "main_wrong": main_wrong_answer(row) or "暂无明显集中错误",
                "level": level,
                "class": get_rate_class(accuracy),
            }
        )
    return items


def build_weak_tags(profiles: List[KnowledgeProfile], top_n: int = 10) -> List[Dict[str, object]]:
    tag_profiles: Dict[str, List[KnowledgeProfile]] = defaultdict(list)
    for profile in profiles:
        tag_profiles[profile.tag].append(profile)
    rows = []
    for tag, items in tag_profiles.items():
        mastery = round(statistics.mean(item.mastery for item in items), 2)
        rows.append({"label": tag, "value": mastery, "display": percent(mastery), "class": get_rate_class(mastery)})
    return sorted(rows, key=lambda item: (float(item["value"]), str(item["label"])))[:top_n]


def build_abnormal_items(item_analysis_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    items = []
    for row in item_analysis_rows:
        badges = []
        blank_rate = float(row.get("blank_rate", 0))
        invalid_rate = float(row.get("invalid_rate", 0))
        partial_rate = float(row.get("partial_rate", 0))
        if blank_rate >= 20:
            badges.append(("空白较多", "badge-warning"))
        if invalid_rate >= 10:
            badges.append(("作答异常", "badge-danger"))
        if partial_rate >= 20:
            badges.append(("漏选较多", "badge-warning"))
        if badges:
            items.append(
                {
                    "question": row.get("question", ""),
                    "blank_rate": blank_rate,
                    "invalid_rate": invalid_rate,
                    "partial_rate": partial_rate,
                    "badges": badges,
                }
            )
    return items


def build_teaching_suggestions(item_analysis_rows: List[Dict[str, object]], profiles: List[KnowledgeProfile]) -> List[Dict[str, str]]:
    suggestions: List[Dict[str, str]] = []
    for row in item_analysis_rows:
        question = row.get("question", "")
        accuracy = float(row.get("accuracy", 0))
        blank_rate = float(row.get("blank_rate", 0))
        invalid_rate = float(row.get("invalid_rate", 0))
        partial_rate = float(row.get("partial_rate", 0))
        if accuracy < 40:
            suggestions.append({"badge": "重点讲评", "class": "badge-danger", "text": f"第 {question} 题正确率较低，建议重点讲评。"})
        elif accuracy < 60:
            suggestions.append({"badge": "课堂订正", "class": "badge-warning", "text": f"第 {question} 题正确率中等偏低，建议课堂订正。"})
        if blank_rate >= 20:
            suggestions.append({"badge": "时间/难度", "class": "badge-warning", "text": f"第 {question} 题空白率较高，可能存在时间不足或题目难度偏高。"})
        if partial_rate >= 20:
            suggestions.append({"badge": "漏选问题", "class": "badge-warning", "text": f"第 {question} 题部分得分较多，可能存在漏选或理解不完整。"})
        if invalid_rate >= 10:
            suggestions.append({"badge": "作答异常", "class": "badge-danger", "text": f"第 {question} 题作答格式异常较多，建议检查答题卡或识别结果。"})

    weak_tags = build_weak_tags(profiles, top_n=10)
    for row in weak_tags:
        if float(row["value"]) < 60:
            suggestions.append({"badge": "知识点薄弱", "class": "badge-info", "text": f"知识点【{row['label']}】平均掌握率较低，建议后续针对性巩固。"})
    return suggestions[:18]


def advanced_dashboard_css() -> str:
    return """
:root{--bg:#f5f7fb;--card:#fff;--line:#e6eaf2;--text:#1f2937;--muted:#667085;--blue:#2f6fed;--green:#16a34a;--orange:#f59e0b;--red:#ef4444;--shadow:0 10px 26px rgba(31,41,55,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.55}
.report-shell{max-width:1200px;margin:0 auto;padding:28px}.report-header{background:linear-gradient(135deg,#fff,#eef5ff);border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:var(--shadow);margin-bottom:18px}
.report-header h1{margin:0 0 10px;font-size:30px}.meta-line{display:flex;flex-wrap:wrap;gap:10px 18px;color:var(--muted)}
.metric-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:18px 0}.metric-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow)}
.metric-card .label{color:var(--muted);font-size:14px}.metric-card .value{font-size:28px;font-weight:750;margin:4px 0}.metric-card .hint{color:var(--muted);font-size:13px}
.dashboard-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.chart-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow);min-width:0}
.chart-card.wide{grid-column:1/-1}.chart-card h2{font-size:19px;margin:0 0 6px}.chart-desc{color:var(--muted);margin:0 0 16px}.empty{color:var(--muted);background:#f8fafc;border:1px dashed #cbd5e1;border-radius:12px;padding:18px;text-align:center}
.vertical-scroll{overflow-x:auto;padding-top:16px}.vertical-chart{display:flex;align-items:flex-end;gap:14px;min-height:230px;min-width:max-content;border-left:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px 12px 10px}
.vbar{width:72px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;min-height:190px}.vbar-value{font-weight:700;margin-bottom:6px}.vbar-fill{width:42px;border-radius:10px 10px 4px 4px;background:var(--blue);min-height:4px}.vbar-fill.danger{background:var(--red)}.vbar-fill.warning{background:var(--orange)}.vbar-fill.normal{background:var(--blue)}.vbar-fill.good{background:var(--green)}.vbar-label{margin-top:8px;color:var(--muted);font-size:13px;text-align:center;white-space:nowrap}
.bar-chart{display:flex;flex-direction:column;gap:12px}.bar-row{display:grid;grid-template-columns:minmax(92px,160px) 1fr 74px;gap:12px;align-items:center}.bar-label{font-weight:650;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{height:16px;background:#edf2f7;border-radius:999px;overflow:hidden}.bar-fill{height:100%;background:var(--blue);border-radius:999px}.bar-fill.danger{background:var(--red)}.bar-fill.warning{background:var(--orange)}.bar-fill.normal{background:var(--blue)}.bar-fill.good{background:var(--green)}.bar-value{text-align:right;font-weight:700}
.wrong-list{display:flex;flex-direction:column;gap:12px}.wrong-item{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fbfdff}.wrong-head{display:flex;justify-content:space-between;gap:12px;font-weight:750}.wrong-item.danger{border-color:#fecaca;background:#fff7f7}.wrong-item.warning{border-color:#fed7aa;background:#fffaf2}.wrong-meta{color:var(--muted);font-size:14px;margin-top:6px}
.compact-table{width:100%;border-collapse:collapse}.compact-table th,.compact-table td{border-bottom:1px solid var(--line);padding:9px;text-align:left}.compact-table th{color:var(--muted);font-weight:700;background:#f8fafc}.badge{display:inline-block;border-radius:999px;padding:4px 9px;font-size:12px;font-weight:700;margin:2px;background:#e0ecff;color:#1d4ed8}.badge-danger{background:#fee2e2;color:#b91c1c}.badge-warning{background:#fef3c7;color:#a16207}.badge-info{background:#dbeafe;color:#1d4ed8}.badge-good{background:#dcfce7;color:#166534}
.suggestions{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.suggestion-card{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fff}.suggestion-card p{margin:8px 0 0}
.option-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.option-card{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fbfdff}.option-card h3{margin:0 0 8px;font-size:15px}
@media(max-width:980px){.metric-grid{grid-template-columns:repeat(3,1fr)}.dashboard-grid{grid-template-columns:1fr}.suggestions{grid-template-columns:1fr}}
@media(max-width:640px){.report-shell{padding:16px}.metric-grid{grid-template-columns:1fr 1fr}.bar-row{grid-template-columns:80px 1fr 58px}.metric-card .value{font-size:24px}.report-header h1{font-size:24px}}
@media print{body{background:#fff}.report-shell{max-width:none;padding:0}.report-header,.metric-card,.chart-card{box-shadow:none;break-inside:avoid}.chart-card{page-break-inside:avoid}.dashboard-grid{grid-template-columns:1fr}.bar-fill,.vbar-fill{background:#555!important}.badge{border:1px solid #999;background:#fff!important;color:#111!important}}
"""


def render_metric_cards(metrics: List[Dict[str, object]]) -> str:
    return '<section class="metric-grid">' + "".join(
        f"""<div class="metric-card"><div class="label">{html_escape(metric['label'])}</div><div class="value">{html_escape(metric['value'])}</div><div class="hint">{html_escape(metric['hint'])}</div></div>"""
        for metric in metrics
    ) + "</section>"


def render_vertical_bar_chart(title: str, items: List[Dict[str, object]], description: str = "") -> str:
    if not items:
        return '<div class="empty">暂无数据</div>'
    max_value = max(float(item.get("value", 0)) for item in items) or 1
    bars = []
    for item in items:
        value = float(item.get("value", 0))
        height = max(3, value / max_value * 170)
        css_class = item.get("class", "normal")
        display = item.get("display", str(item.get("value", "")))
        bars.append(
            f"""<div class="vbar"><div class="vbar-value">{html_escape(display)}</div><div class="vbar-fill {html_escape(css_class)}" style="height:{height:.2f}px"></div><div class="vbar-label">{html_escape(item.get('label', ''))}</div></div>"""
        )
    return f'<div class="vertical-scroll"><div class="vertical-chart">{"".join(bars)}</div></div>'


def render_horizontal_bar_chart(title: str, items: List[Dict[str, object]], description: str = "") -> str:
    if not items:
        return '<div class="empty">暂无数据</div>'
    rows = []
    for item in items:
        value = float(item.get("value", 0))
        rows.append(
            f"""<div class="bar-row"><div class="bar-label" title="{html_escape(item.get('label', ''))}">{html_escape(item.get('label', ''))}</div><div class="bar-track"><div class="bar-fill {html_escape(item.get('class', 'normal'))}" style="width:{max(0, min(100, value)):.2f}%"></div></div><div class="bar-value">{html_escape(item.get('display', percent(value)))}</div></div>"""
        )
    return f'<div class="bar-chart">{"".join(rows)}</div>'


def render_wrong_top(items: List[Dict[str, object]]) -> str:
    if not items:
        return '<div class="empty">暂无题目分析数据</div>'
    cards = []
    for item in items:
        cards.append(
            f"""<div class="wrong-item {html_escape(item['class'])}"><div class="wrong-head"><span>第 {html_escape(item['question'])} 题</span><span>{html_escape(item['level'])}</span></div><div class="wrong-meta">正确率 {percent(item['accuracy'])} · 空白率 {percent(item['blank_rate'])} · 主要错误答案：{html_escape(item['main_wrong'])}</div><div class="bar-track" style="margin-top:10px"><div class="bar-fill {html_escape(item['class'])}" style="width:{max(0, min(100, float(item['accuracy']))):.2f}%"></div></div></div>"""
        )
    return f'<div class="wrong-list">{"".join(cards)}</div>'


def render_abnormal_table(items: List[Dict[str, object]]) -> str:
    if not items:
        return '<div class="empty">本次考试未发现明显作答异常</div>'
    rows = []
    for item in items:
        badges = "".join(f'<span class="badge {html_escape(css)}">{html_escape(text)}</span>' for text, css in item["badges"])
        rows.append(
            f"<tr><td>Q{html_escape(item['question'])}</td><td>{percent(item['blank_rate'])}</td><td>{percent(item['invalid_rate'])}</td><td>{percent(item['partial_rate'])}</td><td>{badges}</td></tr>"
        )
    return f'<table class="compact-table"><thead><tr><th>题号</th><th>空白率</th><th>非法率</th><th>部分得分率</th><th>提醒</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'


def render_suggestion_cards(suggestions: List[Dict[str, str]]) -> str:
    if not suggestions:
        return '<div class="empty">暂无需要特别讲评的建议</div>'
    return '<div class="suggestions">' + "".join(
        f"""<div class="suggestion-card"><span class="badge {html_escape(item['class'])}">{html_escape(item['badge'])}</span><p>{html_escape(item['text'])}</p></div>"""
        for item in suggestions
    ) + "</div>"


def render_option_distribution(item_rows: List[Dict[str, object]]) -> str:
    if not item_rows:
        return '<div class="empty">暂无题目分析数据</div>'
    cards = []
    for row in item_rows:
        distribution = row.get("distribution", {})
        if not isinstance(distribution, dict):
            distribution = {}
        lines = "".join(
            f"""<div class="bar-row" style="grid-template-columns:60px 1fr 44px"><div class="bar-label">{html_escape(option)}</div><div class="bar-track"><div class="bar-fill normal" style="width:{min(100, int(count) * 20):.2f}%"></div></div><div class="bar-value">{html_escape(count)}</div></div>"""
            for option, count in sorted(distribution.items())
        )
        body = lines or '<div class="empty">暂无数据</div>'
        cards.append(f'<div class="option-card"><h3>Q{html_escape(row.get("question", ""))}</h3>{body}</div>')
    return f'<div class="option-grid">{"".join(cards)}</div>'


def write_advanced_dashboard(path: Path, meta: ExamMeta, results: List[StudentResult], profiles: List[KnowledgeProfile], validation_rows: List[Dict[str, object]], item_rows: List[Dict[str, object]]) -> None:
    stats = basic_stats(results)
    metrics = [
        {"label": "参考人数", "value": len(results), "hint": "参与本次批改的学生数"},
        {"label": "平均分", "value": stats["average"], "hint": "班级总体水平"},
        {"label": "最高分", "value": stats["highest"], "hint": "本次最高成绩"},
        {"label": "最低分", "value": stats["lowest"], "hint": "需重点关注"},
        {"label": "及格率", "value": percent(stats["pass_rate"]), "hint": "60% 及以上"},
        {"label": "优秀率", "value": percent(stats["excellent_rate"]), "hint": "90% 及以上"},
    ]
    score_distribution = build_score_distribution(results)
    accuracy_items = build_question_accuracy_items(item_rows)
    weak_items = build_weak_items(item_rows)
    weak_tags = build_weak_tags(profiles)
    abnormal_items = build_abnormal_items(item_rows)
    suggestions = build_teaching_suggestions(item_rows, profiles)
    warning_rows = [row for row in validation_rows if row.get("severity") in {"warning", "error"}]
    warning_html = render_table(
        ["级别", "范围", "项目", "提醒"],
        [[row.get("severity", ""), row.get("scope", ""), row.get("item", ""), row.get("message", "")] for row in warning_rows],
    ) if warning_rows else '<div class="empty">暂无未匹配、低置信度或异常答案提醒</div>'
    weak_tag_body = render_horizontal_bar_chart("班级薄弱知识点", weak_tags) if weak_tags else '<div class="empty">暂无知识点数据</div>'
    generated_at = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>高级学情分析报告 - {html_escape(meta.exam_name)}</title><style>{advanced_dashboard_css()}</style></head>
<body><main class="report-shell">
<header class="report-header"><h1>高级学情分析报告</h1><div class="meta-line"><span>考试名称：{html_escape(meta.exam_name)}</span><span>班级：{html_escape(meta.class_name or "未填写")}</span><span>科目：{html_escape(meta.subject or "未填写")}</span><span>考试日期：{html_escape(meta.exam_date)}</span><span>生成时间：{html_escape(generated_at)}</span></div></header>
{render_metric_cards(metrics)}
<section class="dashboard-grid">
<article class="chart-card"><h2>成绩分布</h2><p class="chart-desc">查看班级成绩集中区间。</p>{render_vertical_bar_chart("成绩分布", score_distribution)}</article>
<article class="chart-card"><h2>每题正确率</h2><p class="chart-desc">低于 40% 标红，40%-60% 标橙。</p>{render_vertical_bar_chart("每题正确率", accuracy_items)}</article>
<article class="chart-card"><h2>易错题 Top 5</h2><p class="chart-desc">按正确率从低到高排序。</p>{render_wrong_top(weak_items)}</article>
<article class="chart-card"><h2>班级薄弱知识点</h2><p class="chart-desc">按全班平均掌握率从低到高展示 Top 10。</p>{weak_tag_body}</article>
<article class="chart-card"><h2>答题异常情况</h2><p class="chart-desc">空白、非法答案、漏选较多的题会被标记。</p>{render_abnormal_table(abnormal_items)}</article>
<article class="chart-card"><h2>教学讲评建议</h2><p class="chart-desc">把题目与知识点数据转换成可执行建议。</p>{render_suggestion_cards(suggestions)}</article>
<article class="chart-card wide"><h2>每题选项分布</h2><p class="chart-desc">用于观察学生主要误选项或空白集中情况。</p>{render_option_distribution(item_rows)}</article>
<article class="chart-card wide"><h2>未匹配、低置信度、异常答案等提醒</h2>{warning_html}</article>
</section>
</main></body></html>"""
    path.write_text(html, encoding="utf-8")


def report_link(path: Path, label: str, css_class: str) -> str:
    if path.exists():
        return f'<a class="btn {css_class}" href="{html_escape(path.name)}">{html_escape(label)}</a>'
    return f'<div class="btn {css_class} disabled">{html_escape(label)}<span>文件暂未生成</span></div>'


def write_report_index(
    path: Path,
    meta: ExamMeta,
    simple_report_path: Path,
    advanced_dashboard_path: Path,
    simple_score_report_path: Path,
) -> None:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>批改完成</title>
<style>
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;background:#f5f7fb;color:#172033}}
.shell{{max-width:820px;margin:60px auto;padding:32px}}
.card{{background:#fff;border-radius:18px;padding:32px;box-shadow:0 16px 40px rgba(15,23,42,.08)}}
h1{{margin:0 0 10px;font-size:30px}}
.meta{{color:#667085;margin-bottom:28px;line-height:1.8;font-size:16px}}
.actions{{display:grid;gap:16px}}
.btn{{display:block;padding:18px 22px;border-radius:14px;text-decoration:none;font-size:18px;font-weight:700}}
.btn span{{display:block;margin-top:5px;font-size:14px;font-weight:500}}
.btn-primary{{background:#2563eb;color:white}}
.btn-success{{background:#16a34a;color:white}}
.btn-outline{{background:white;color:#172033;border:1px solid #d8dee8}}
.disabled{{background:#eef2f7;color:#667085;border:1px solid #d8dee8;cursor:not-allowed}}
.hint{{margin-top:24px;color:#667085;font-size:14px;line-height:1.7}}
@media (max-width:640px){{.shell{{margin:20px auto;padding:16px}}.card{{padding:24px}}h1{{font-size:26px}}.btn{{font-size:17px}}}}
</style>
</head>
<body>
<div class="shell">
  <div class="card">
    <h1>本次批改完成</h1>
    <div class="meta">
      考试：{html_escape(meta.exam_name or "未填写")}<br>
      班级：{html_escape(meta.class_name or "未填写")}<br>
      科目：{html_escape(meta.subject or "未填写")}<br>
      日期：{html_escape(meta.exam_date or "未填写")}
    </div>
    <div class="actions">
      {report_link(simple_report_path, "查看普通版报告", "btn-primary")}
      {report_link(advanced_dashboard_path, "查看高级学情分析", "btn-success")}
      {report_link(simple_score_report_path, "打开简单成绩表", "btn-outline")}
    </div>
    <div class="hint">普通老师建议先查看“普通版报告”。需要深入分析时，再打开“高级学情分析”。</div>
  </div>
</div>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def safe_slug(value: str) -> str:
    text = (value or "exam").strip().lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_\-\u4e00-\u9fff]+", "", text)
    return text or "exam"


def archive_reports(source_dir: Path, archive_root: Path, meta: ExamMeta, report_paths: List[Path]) -> Path:
    archive_dir = archive_root / f"{safe_slug(meta.exam_date)}_{safe_slug(meta.exam_name)}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "exam_name": meta.exam_name,
        "class_name": meta.class_name,
        "subject": meta.subject,
        "exam_date": meta.exam_date,
        "source_report_dir": str(source_dir.resolve()),
    }
    (archive_dir / "exam_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for report_path in report_paths:
        if report_path.exists():
            shutil.copy2(str(report_path), str(archive_dir / report_path.name))
    return archive_dir


def print_console_report(results: List[StudentResult]) -> None:
    if not results:
        print("No submissions found.")
        return
    scores = [result.score for result in results]
    print(f"Students: {len(results)}")
    print(f"Average: {statistics.mean(scores):.2f}")
    print(f"Median: {statistics.median(scores):.2f}")
    print(f"Max: {max(scores):.2f}")
    print(f"Min: {min(scores):.2f}")
    print()
    print("Top students:")
    for result in sorted(results, key=lambda item: item.score, reverse=True)[:5]:
        print(f"  {result.student_id}\t{result.name}\t{result.score:.2f}/{result.max_score:.2f}\t{result.percent:.2f}%")


def create_sample_files(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    key_path = directory / "answer_key_sample.csv"
    submissions_path = directory / "submissions_sample.csv"
    bank_path = directory / "question_bank_sample.csv"
    if not key_path.exists():
        key_path.write_text(
            "question,question_id,answer,points,partial_credit,partial_points,tags,difficulty\n"
            "1,B001,A,1,false,,linear_equation,1\n"
            "2,B003,BD,2,true,1,function_concept,3\n"
            "3,B004,C,1,false,,geometry_area,2\n",
            encoding="utf-8-sig",
        )
    if not submissions_path.exists():
        submissions_path.write_text(
            "student_id,name,Q1,Q2,Q3\n"
            "S001,Student One,A,B,C\n"
            "S002,Student Two,B,BD,\n",
            encoding="utf-8-sig",
        )
    if not bank_path.exists():
        bank_path.write_text(
            "question_id,stem,answer,tags,difficulty\n"
            "B001,Solve a basic linear equation.,A,linear_equation,1\n"
            "B002,Choose an equivalent equation form.,C,linear_equation,2\n"
            "B003,Identify the correct function statements.,BD,function_concept,3\n"
            "B004,Find the area from the given dimensions.,C,geometry_area,2\n",
            encoding="utf-8-sig",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grade objective-question submissions from CSV files.")
    parser.add_argument("--answer-key", type=Path, help="CSV answer key file.")
    parser.add_argument("--submissions", type=Path, help="CSV student submissions file.")
    parser.add_argument("--question-bank", type=Path, help="Optional CSV question bank for practice recommendations.")
    parser.add_argument("--out-dir", type=Path, default=Path("reports"), help="Directory for exported reports.")
    parser.add_argument("--make-samples", action="store_true", help="Create sample CSV files in the output directory.")
    parser.add_argument("--weak-threshold", type=float, default=70.0, help="Mastery percentage below this value is treated as weak.")
    parser.add_argument("--practice-per-tag", type=int, default=3, help="Recommended practice questions per weak knowledge point.")
    parser.add_argument("--exam-name", default="demo_exam", help="Exam name used in class reports and archives.")
    parser.add_argument("--class-name", default="", help="Class name used in class reports and archives.")
    parser.add_argument("--subject", default="", help="Subject name used in class reports and archives.")
    parser.add_argument("--exam-date", default=date.today().isoformat(), help="Exam date, usually YYYY-MM-DD.")
    parser.add_argument("--archive-root", type=Path, default=Path("exams"), help="Directory that stores archived exam reports.")
    parser.add_argument("--no-archive", action="store_true", help="Do not copy reports into the exam archive directory.")
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
    answer_key = load_answer_key(args.answer_key)
    submissions = load_submissions(args.submissions, answer_key)
    results = grade_all(answer_key, submissions)
    meta = ExamMeta(
        exam_name=args.exam_name,
        class_name=args.class_name,
        subject=args.subject,
        exam_date=args.exam_date,
    )
    summary_path = args.out_dir / "summary.csv"
    detail_path = args.out_dir / "detail.csv"
    item_analysis_path = args.out_dir / "item_analysis.csv"
    knowledge_profile_path = args.out_dir / "knowledge_profile.csv"
    practice_path = args.out_dir / "practice_recommendations.csv"
    class_report_path = args.out_dir / "class_report.csv"
    validation_path = args.out_dir / "validation_report.csv"
    student_report_path = args.out_dir / "student_report.csv"
    workbook_path = args.out_dir / "exam_report.xlsx"
    simple_report_path = args.out_dir / "simple_report.html"
    advanced_dashboard_path = args.out_dir / "advanced_dashboard.html"
    simple_score_workbook_path = args.out_dir / "simple_score_report.xlsx"
    index_path = args.out_dir / "index.html"

    write_summary(summary_path, results)
    write_detail(detail_path, answer_key, results)
    write_item_analysis(item_analysis_path, answer_key, results)
    profiles = build_knowledge_profiles(answer_key, results, weak_threshold=args.weak_threshold)
    write_knowledge_profiles(knowledge_profile_path, profiles)
    question_bank = None
    if args.question_bank:
        question_bank = load_question_bank(args.question_bank)
        already_correct = build_correct_question_ids(answer_key, results)
        target_difficulties = build_target_difficulties(answer_key, results)
        practice_rows = recommend_practice(
            profiles,
            question_bank,
            per_tag=args.practice_per_tag,
            already_correct=already_correct,
            target_difficulties=target_difficulties,
        )
        write_practice_recommendations(practice_path, practice_rows)
    else:
        write_practice_recommendations(practice_path, [])
    class_rows = build_class_report(answer_key, results, profiles, meta)
    write_class_report(class_report_path, class_rows)
    validation_rows = build_validation_report(answer_key, submissions, results, profiles, question_bank)
    write_validation_report(validation_path, validation_rows)
    write_student_report(student_report_path, results, profiles)
    simple_rows = simple_score_rows(results)
    item_rows = item_stats(answer_key, results)
    write_simple_score_workbook(simple_score_workbook_path, simple_rows)
    write_simple_report(simple_report_path, meta, answer_key, results, simple_rows, item_rows)
    write_advanced_dashboard(advanced_dashboard_path, meta, results, profiles, validation_rows, item_rows)
    write_report_index(index_path, meta, simple_report_path, advanced_dashboard_path, simple_score_workbook_path)
    report_files = [
        ("summary", summary_path),
        ("detail", detail_path),
        ("item_analysis", item_analysis_path),
        ("knowledge_profile", knowledge_profile_path),
        ("class_report", class_report_path),
        ("validation", validation_path),
        ("student_report", student_report_path),
    ]
    report_files.append(("practice", practice_path))
    write_workbook(workbook_path, report_files)
    archived_dir = None
    if not args.no_archive:
        archived_dir = archive_reports(
            args.out_dir,
            args.archive_root,
            meta,
            [path for _name, path in report_files]
            + [workbook_path, simple_report_path, advanced_dashboard_path, simple_score_workbook_path, index_path],
        )
    print()
    print("批改完成。")
    print()
    print("请打开：")
    print(index_path)
    print()
    print("如果需要：")
    print(f"普通版报告：{simple_report_path}")
    print(f"高级学情分析：{advanced_dashboard_path}")
    print(f"简单成绩表：{simple_score_workbook_path}")
    print()
    print("数据底稿已保存到：")
    print(f"{args.out_dir}/")
    if archived_dir:
        print()
        print("考试归档已保存到：")
        print(f"{archived_dir}/")
    return 0

    print_console_report(results)
    print()
    print("批改完成。")
    print(f"普通版报告：{simple_report_path}")
    print(f"高级学情分析：{advanced_dashboard_path}")
    print(f"简单成绩表：{simple_score_workbook_path}")
    print(f"数据底稿目录：{args.out_dir}/")
    if archived_dir:
        print(f"Archive written to {archived_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
