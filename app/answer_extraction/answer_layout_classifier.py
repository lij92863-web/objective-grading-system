from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.answer_extraction.document_model import DocumentModel, DocumentTable
from app.answer_extraction.student_answer_grid_detector import detect_student_answer_grid


class AnswerLayout(str, Enum):
    BOXED_TABLE = "boxed_table"
    ITEMIZED_EXPLANATION = "itemized_explanation"
    MIXED = "mixed"
    NONE = "none"
    UNKNOWN = "unknown"


class TableSemanticType(str, Enum):
    ANSWER_KEY_TABLE = "answer_key_table"
    STUDENT_ANSWER_GRID = "student_answer_grid"
    SCORE_TABLE = "score_table"
    OTHER_TABLE = "other_table"
    UNKNOWN_TABLE = "unknown_table"


@dataclass(frozen=True)
class AnswerLayoutResult:
    layout: AnswerLayout
    confidence: float
    table_semantics: dict[str, TableSemanticType] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "answer_layout": self.layout.value,
            "confidence": self.confidence,
            "table_semantics": {k: v.value for k, v in self.table_semantics.items()},
            "reasons": list(self.reasons),
        }


def classify_table_semantic(table: DocumentTable, document: DocumentModel | None = None) -> TableSemanticType:
    if detect_student_answer_grid(table, document).is_student_answer_grid:
        return TableSemanticType.STUDENT_ANSWER_GRID
    text = "\n".join(" ".join(row) for row in table.grid())
    if "题号" in text and "答案" in text:
        return TableSemanticType.ANSWER_KEY_TABLE
    if "得分" in text or "评分" in text:
        return TableSemanticType.SCORE_TABLE
    return TableSemanticType.OTHER_TABLE


def classify_answer_layout(document: DocumentModel) -> AnswerLayoutResult:
    text = document.all_text()
    semantics = {table.table_id: classify_table_semantic(table, document) for table in document.sorted_tables()}
    has_boxed = TableSemanticType.ANSWER_KEY_TABLE in semantics.values()
    has_itemized = any(token in text for token in ("【答案】", "故选", "故答案为", "答案:"))
    reasons: list[str] = []
    if has_boxed:
        reasons.append("answer key table")
    if has_itemized:
        reasons.append("itemized answer phrases")
    if has_boxed and has_itemized:
        return AnswerLayoutResult(AnswerLayout.MIXED, 0.9, semantics, reasons)
    if has_boxed:
        return AnswerLayoutResult(AnswerLayout.BOXED_TABLE, 0.9, semantics, reasons)
    if has_itemized:
        return AnswerLayoutResult(AnswerLayout.ITEMIZED_EXPLANATION, 0.86, semantics, reasons)
    if any(token in text for token in ("单选题", "单项选择", "多选题", "多项选择", "填空题", "解答题")):
        return AnswerLayoutResult(AnswerLayout.NONE, 0.8, semantics, reasons)
    return AnswerLayoutResult(AnswerLayout.UNKNOWN, 0.3, semantics, reasons)
