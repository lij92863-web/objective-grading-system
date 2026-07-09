"""Ground-truth model for a single synthetic answer sheet.

The :class:`GroundTruth` records exactly what a generated sheet *should* contain.
Because the generator only performs **known, invertible transformations** (a
filled bubble, a weak fill, a multi-fill, an erased fill, or nothing -- plus
optional geometric/noise perturbations), the ground truth is fully trustworthy:
the image is literally rendered from these values (constitution: "fixture
truthfulness guard" must prove the image matches its ground truth).

``mark_type`` is restricted to a fixed enum-like set
``("strong", "weak", "multi", "erased", "none")``. Any other value is rejected on
deserialization so a malformed ground truth can never silently pass a guard.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

__all__ = [
    "MARK_TYPES",
    "STRONG",
    "WEAK",
    "MULTI",
    "ERASED",
    "NONE",
    "AnswerRecord",
    "GroundTruth",
]

# Canonical mark-type vocabulary (see constitution / perturbation spec).
STRONG: str = "strong"
WEAK: str = "weak"
MULTI: str = "multi"
ERASED: str = "erased"
NONE: str = "none"
MARK_TYPES: "tuple[str, ...]" = (STRONG, WEAK, MULTI, ERASED, NONE)


@dataclass
class AnswerRecord:
    """Ground truth for one question's answer bubble(s)."""

    question: int
    selected: Optional[str]
    mark_type: str
    expected_option: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "selected": self.selected,
            "mark_type": self.mark_type,
            "expected_option": self.expected_option,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnswerRecord":
        mark_type = data.get("mark_type")
        if mark_type not in MARK_TYPES:
            raise ValueError(
                f"invalid mark_type {mark_type!r}; expected one of {MARK_TYPES}"
            )
        return cls(
            question=int(data["question"]),
            selected=data.get("selected"),
            mark_type=mark_type,
            expected_option=data.get("expected_option"),
        )


@dataclass
class GroundTruth:
    """Full ground truth for one synthetic sheet."""

    sheet_id: str
    template_id: str
    student: Dict[str, str]
    answers: List[AnswerRecord]
    perturbation: str
    seed: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sheet_id": self.sheet_id,
            "template_id": self.template_id,
            "student": dict(self.student),
            "answers": [a.to_dict() for a in self.answers],
            "perturbation": self.perturbation,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroundTruth":
        raw_answers = data.get("answers", [])
        answers: List[AnswerRecord] = []
        for item in raw_answers:
            # AnswerRecord.from_dict validates mark_type and raises ValueError
            # on anything outside MARK_TYPES.
            answers.append(AnswerRecord.from_dict(item))
        return cls(
            sheet_id=str(data["sheet_id"]),
            template_id=str(data.get("template_id", "")),
            student=dict(data.get("student", {})),
            answers=answers,
            perturbation=str(data.get("perturbation", "clean")),
            seed=int(data.get("seed", 0)),
        )
