import dataclasses
from collections import Counter
from enum import Enum

from .roster_mapping import RosterColumnMapping


class RosterImportState(str, Enum):
    UPLOADED = "UPLOADED"
    COLUMN_MAPPING_REQUIRED = "COLUMN_MAPPING_REQUIRED"
    VALIDATED = "VALIDATED"
    BLOCKED = "BLOCKED"
    IMPORTED = "IMPORTED"


@dataclasses.dataclass(frozen=True)
class Student:
    student_id: str
    class_id: str
    student_no: str
    name: str
    aliases: tuple[str, ...]
    status: str
    created_at: str
    updated_at: str


@dataclasses.dataclass(frozen=True)
class RosterIssue:
    severity: str
    row_number: int
    code: str
    message: str


@dataclasses.dataclass(frozen=True)
class RosterImportResult:
    state: RosterImportState
    student_count: int
    warnings: tuple[RosterIssue, ...]
    blocking: tuple[RosterIssue, ...]
    headers: tuple[str, ...] = ()
    mapping: RosterColumnMapping | None = None


def validate_rows(
    rows: list[dict[str, object]],
    mapping: RosterColumnMapping,
) -> tuple[list[tuple[str, str]], list[RosterIssue], list[RosterIssue]]:
    students: list[tuple[str, str]] = []
    warnings: list[RosterIssue] = []
    blocking: list[RosterIssue] = []
    for row_number, row in enumerate(rows, start=2):
        student_no = str(row.get(mapping.student_no_column) or "").strip()
        name = str(row.get(mapping.name_column) or "").strip()
        if not student_no and not name:
            warnings.append(RosterIssue("warning", row_number, "blank_row", "空行已跳过。"))
            continue
        if not student_no:
            blocking.append(RosterIssue("error", row_number, "missing_student_no", "学号不能为空。"))
        if not name:
            blocking.append(RosterIssue("error", row_number, "missing_name", "姓名不能为空。"))
        if student_no and name:
            students.append((student_no, name))

    number_counts = Counter(number for number, _ in students)
    for number, count in number_counts.items():
        if count > 1:
            blocking.append(RosterIssue("error", 0, "duplicate_student_no", f"学号 {number} 重复。"))
    name_counts = Counter(name for _, name in students)
    for name, count in name_counts.items():
        if count > 1:
            warnings.append(RosterIssue("warning", 0, "duplicate_name", f"姓名 {name} 重复，请确认。"))
    return students, warnings, blocking
