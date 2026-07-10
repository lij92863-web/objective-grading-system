"""Immutable contracts for a deterministic grading run."""

import dataclasses
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from app.domain.grading.models import AnswerKey, StudentResult, Submission
from app.domain.grading.precheck import PrecheckReport


NON_OVERRIDABLE_ISSUE_CODES = frozenset({
    "missing_answer_key", "missing_expected_answer", "conflicting_duplicate_question",
    "duplicate_student_identity", "unconfirmed_recognition_draft", "unknown_question_type",
    "unknown_question_status", "invalid_domain_model", "legacy_external_blocker",
})
OVERRIDABLE_ISSUE_CODES = frozenset({"missing_question_bank"})
KNOWN_OVERRIDE_CODES = NON_OVERRIDABLE_ISSUE_CODES | OVERRIDABLE_ISSUE_CODES


@dataclasses.dataclass(frozen=True)
class ExamMetadata:
    exam_name: str = "demo_exam"
    class_name: str = ""
    subject: str = ""
    exam_date: str = ""


@dataclasses.dataclass(frozen=True)
class ReportPolicy:
    weak_threshold: float = 70.0
    practice_per_tag: int = 3


@dataclasses.dataclass(frozen=True)
class ArchivePolicy:
    archive_root: Optional[Path] = None
    enabled: bool = True


@dataclasses.dataclass(frozen=True)
class ValidationPolicy:
    strict_drafts: bool = True
    external_issues: Tuple[object, ...] = ()


@dataclasses.dataclass(frozen=True)
class GradingOverride:
    allowed_issue_codes: Tuple[str, ...]
    actor: str
    reason: str
    created_at: str

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValueError("override actor is required")
        if not self.reason.strip():
            raise ValueError("override reason is required")
        unknown = set(self.allowed_issue_codes) - KNOWN_OVERRIDE_CODES
        if unknown:
            raise ValueError(f"unknown override issue code(s): {sorted(unknown)}")
        forbidden = set(self.allowed_issue_codes) & NON_OVERRIDABLE_ISSUE_CODES
        if forbidden:
            raise ValueError(f"non-overridable issue code(s): {sorted(forbidden)}")


@dataclasses.dataclass(frozen=True)
class GradingRunRequest:
    answer_key_path: Path
    submissions_path: Path
    output_dir: Path
    question_bank_path: Optional[Path] = None
    exam_metadata: ExamMetadata = dataclasses.field(default_factory=ExamMetadata)
    report_policy: ReportPolicy = dataclasses.field(default_factory=ReportPolicy)
    archive_policy: ArchivePolicy = dataclasses.field(default_factory=ArchivePolicy)
    validation_policy: ValidationPolicy = dataclasses.field(default_factory=ValidationPolicy)
    override: Optional[GradingOverride] = None
    run_id: Optional[str] = None
    source_files: Mapping[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "answer_key_path", Path(self.answer_key_path))
        object.__setattr__(self, "submissions_path", Path(self.submissions_path))
        object.__setattr__(self, "output_dir", Path(self.output_dir))
        object.__setattr__(self, "source_files", MappingProxyType(dict(self.source_files)))


class GradingRunStatus(str, Enum):
    BLOCKED = "blocked"
    GRADED = "graded"


@dataclasses.dataclass(frozen=True)
class GradingStats:
    student_count: int
    question_count: int
    total_points: float


@dataclasses.dataclass(frozen=True)
class GradingRunResult:
    status: GradingRunStatus
    run_id: str
    precheck: PrecheckReport
    generated_files: Tuple[Path, ...] = ()
    archive_dir: Optional[Path] = None
    stats: Optional[GradingStats] = None
    warnings: Tuple[str, ...] = ()
    answer_key: Optional[AnswerKey] = dataclasses.field(default=None, repr=False)
    submissions: Tuple[Submission, ...] = dataclasses.field(default=(), repr=False)
    student_results: Tuple[StudentResult, ...] = dataclasses.field(default=(), repr=False)
