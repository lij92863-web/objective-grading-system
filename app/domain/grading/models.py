"""Stable grading models.

The first fields mirror the legacy dataclasses so existing reports and CSV
workflows can keep using positional construction where they already do.
"""

import dataclasses
from enum import Enum
from types import MappingProxyType
from typing import Dict, FrozenSet, Mapping, Optional, Tuple


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    BLANK = "blank"


@dataclasses.dataclass(frozen=True)
class DuplicateQuestionIssue:
    question_number: int
    row_numbers: Tuple[int, ...]
    raw_answers: Tuple[str, ...]
    raw_points: Tuple[str, ...]
    raw_types: Tuple[str, ...]
    is_conflicting: bool


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
    question_type: str = ""


@dataclasses.dataclass(frozen=True)
class AnswerKey:
    questions: Tuple[QuestionSpec, ...]
    duplicate_questions: Tuple[int, ...] = ()
    duplicate_issues: Tuple[DuplicateQuestionIssue, ...] = ()

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
    answers: Mapping[int, FrozenSet[str]]
    raw_answers: Mapping[int, str]
    extra_questions: Tuple[int, ...]
    row_number: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "answers", MappingProxyType(dict(self.answers)))
        object.__setattr__(self, "raw_answers", MappingProxyType(dict(self.raw_answers)))


@dataclasses.dataclass(frozen=True)
class SingleQuestionScore:
    question_number: int
    score: float
    max_score: float
    status: str
    question_type: str
    expected: FrozenSet[str]
    actual: FrozenSet[str]
    raw_actual: str = ""
    student_answer: str = ""
    normalized_answer: str = ""
    correct_answer: str = ""
    reason: str = ""
    needs_review: bool = False


@dataclasses.dataclass(frozen=True)
class QuestionResult:
    number: int
    expected: FrozenSet[str]
    actual: FrozenSet[str]
    raw_actual: str
    score: float
    max_score: float
    status: str
    question_type: str = ""
    student_answer: str = ""
    normalized_answer: str = ""
    correct_answer: str = ""
    reason: str = ""
    needs_review: bool = False
    confidence: Optional[float] = None
    source: str = ""
    original_answer: str = ""


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
