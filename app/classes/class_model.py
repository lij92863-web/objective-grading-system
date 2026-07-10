import dataclasses
from enum import Enum


class ClassState(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclasses.dataclass(frozen=True)
class ClassRoom:
    class_id: str
    class_name: str
    grade_name: str
    school_year: str
    status: ClassState
    created_at: str
    updated_at: str
