from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SequenceValidationResult:
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)


def validate_question_sequence(numbers: list[int]) -> SequenceValidationResult:
    warnings: list[str] = []
    blocking: list[str] = []
    seen: set[int] = set()
    last = 0
    for number in numbers:
        if number in seen:
            blocking.append("duplicate_question_number")
        if last and number < last:
            blocking.append("question_number_rewind")
        if last and number - last > 5:
            warnings.append("large_question_number_jump")
        seen.add(number)
        last = number
    if numbers:
        missing = sorted(set(range(min(numbers), max(numbers) + 1)) - set(numbers))
        if missing:
            warnings.append("missing_question_number_in_middle")
    return SequenceValidationResult(sorted(set(warnings)), sorted(set(blocking)))
