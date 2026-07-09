"""R35: OMR cell metrics contract."""
from dataclasses import dataclass, field
from typing import List

VALID_OPTIONS = set("ABCDEFGH")


@dataclass
class ChoiceCellMetric:
    question_id: int = 0
    option: str = ""
    dark_ratio: float = 0.0
    mark_area_ratio: float = 0.0
    confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def validate(self) -> list:
        errors = []
        if self.option not in VALID_OPTIONS:
            errors.append(f"INVALID_OPTION:{self.option}")
        if not (0.0 <= self.dark_ratio <= 1.0):
            errors.append(f"INVALID_DARK_RATIO:{self.dark_ratio}")
        if not (0.0 <= self.mark_area_ratio <= 1.0):
            errors.append(f"INVALID_MARK_RATIO:{self.mark_area_ratio}")
        if not (0.0 <= self.confidence <= 1.0):
            errors.append(f"INVALID_CONFIDENCE:{self.confidence}")
        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0
