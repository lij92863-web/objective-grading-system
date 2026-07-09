from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.answer_extraction.answer_layout_classifier import AnswerLayout, AnswerLayoutResult
from app.answer_extraction.file_role_classifier import FileRole, FileRoleResult


class ExtractionStrategy(str, Enum):
    SAME_FILE_BOXED = "same_file_boxed"
    SAME_FILE_ITEMIZED = "same_file_itemized"
    SPLIT_FILE_BOXED = "split_file_boxed"
    SPLIT_FILE_ITEMIZED = "split_file_itemized"
    MIXED_OR_UNKNOWN = "mixed_or_unknown"


@dataclass(frozen=True)
class StrategyResult:
    strategy: ExtractionStrategy
    confidence: float
    reason: str


def choose_strategy(roles: list[FileRoleResult], layouts: list[AnswerLayoutResult]) -> StrategyResult:
    if len(roles) != len(layouts):
        return StrategyResult(ExtractionStrategy.MIXED_OR_UNKNOWN, 0.2, "classifier result mismatch")
    if len(roles) == 1:
        role = roles[0].role
        layout = layouts[0].layout
        if role == FileRole.MIXED_QUESTION_ANSWER and layout in {AnswerLayout.BOXED_TABLE, AnswerLayout.MIXED}:
            return StrategyResult(ExtractionStrategy.SAME_FILE_BOXED, 0.9, "single mixed boxed document")
        if role == FileRole.MIXED_QUESTION_ANSWER and layout == AnswerLayout.ITEMIZED_EXPLANATION:
            return StrategyResult(ExtractionStrategy.SAME_FILE_ITEMIZED, 0.86, "single mixed itemized document")
    if len(roles) == 2:
        role_values = [role.role for role in roles]
        answer_index = next((i for i, role in enumerate(role_values) if role == FileRole.ANSWER_ONLY), None)
        if FileRole.QUESTION_ONLY in role_values and answer_index is not None:
            layout = layouts[answer_index].layout
            if layout in {AnswerLayout.BOXED_TABLE, AnswerLayout.MIXED}:
                return StrategyResult(ExtractionStrategy.SPLIT_FILE_BOXED, 0.9, "split boxed answer document")
            if layout == AnswerLayout.ITEMIZED_EXPLANATION:
                return StrategyResult(ExtractionStrategy.SPLIT_FILE_ITEMIZED, 0.86, "split itemized answer document")
    return StrategyResult(ExtractionStrategy.MIXED_OR_UNKNOWN, 0.2, "safe fallback")
