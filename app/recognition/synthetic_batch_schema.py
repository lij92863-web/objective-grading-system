"""Synthetic batch fixture schema v4."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


REQUIRED_TOP_LEVEL = {"schema_version", "batch_id", "exam_id", "scenario", "students", "items", "expected"}
REQUIRED_STUDENT_FIELDS = {"student_ref", "display_name", "identity_status"}
REQUIRED_ITEM_FIELDS = {
    "student_ref",
    "question_id",
    "question_type",
    "source",
    "omr_status",
    "omr_answer",
    "omr_confidence",
    "qwen_required",
    "qwen_response_kind",
    "expected_decision_status",
    "expected_exception_codes",
}
EXPECTED_FIELDS = {
    "batch_status",
    "total_students",
    "total_items",
    "auto_accepted_items",
    "needs_review_items",
    "blocking_items",
    "qwen_call_count",
    "blocked_by_budget_count",
    "ready_students",
    "needs_review_students",
    "blocked_students",
}
DEFAULT_QWEN_BUDGET = {"enabled": False, "max_calls": 0, "estimated_calls": 0}


@dataclass
class SyntheticBatchFixture:
    schema_version: int
    batch_id: str
    exam_id: str
    scenario: str
    students: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
    qwen_budget: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_QWEN_BUDGET))
    expected: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyntheticBatchFixture":
        validate_synthetic_batch_fixture(data)
        budget = dict(DEFAULT_QWEN_BUDGET)
        budget.update(data.get("qwen_budget") or {})
        return cls(
            schema_version=int(data["schema_version"]),
            batch_id=str(data["batch_id"]),
            exam_id=str(data["exam_id"]),
            scenario=str(data["scenario"]),
            students=list(data["students"]),
            items=list(data["items"]),
            qwen_budget=budget,
            expected=dict(data["expected"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "exam_id": self.exam_id,
            "scenario": self.scenario,
            "students": self.students,
            "items": self.items,
            "qwen_budget": self.qwen_budget,
            "expected": self.expected,
        }


def validate_synthetic_batch_fixture(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("fixture must be a JSON object")
    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        raise ValueError(f"missing required fixture fields: {missing}")
    if not isinstance(data["students"], list) or not data["students"]:
        raise ValueError("students must be a non-empty list")
    if not isinstance(data["items"], list) or not data["items"]:
        raise ValueError("items must be a non-empty list")
    if not isinstance(data["expected"], dict):
        raise ValueError("expected must be an object")
    missing_expected = sorted(EXPECTED_FIELDS - set(data["expected"]))
    if missing_expected:
        raise ValueError(f"missing expected fields: {missing_expected}")
    for field_name in EXPECTED_FIELDS - {"batch_status"}:
        if not isinstance(data["expected"].get(field_name), int):
            raise ValueError(f"expected.{field_name} must be an integer")
    for student in data["students"]:
        missing_student = sorted(REQUIRED_STUDENT_FIELDS - set(student))
        if missing_student:
            raise ValueError(f"missing student fields: {missing_student}")
    for item in data["items"]:
        missing_item = sorted(REQUIRED_ITEM_FIELDS - set(item))
        if missing_item:
            raise ValueError(f"missing item fields: {missing_item}")
        if not isinstance(item["expected_exception_codes"], list):
            raise ValueError("expected_exception_codes must be a list")
    budget = data.get("qwen_budget") or DEFAULT_QWEN_BUDGET
    if not isinstance(budget, dict):
        raise ValueError("qwen_budget must be an object")
    for key in ("enabled", "max_calls", "estimated_calls"):
        if key not in budget:
            raise ValueError(f"qwen_budget missing {key}")
