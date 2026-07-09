from __future__ import annotations

from dataclasses import dataclass, field

from app.answer_extraction.answer_normalizer import normalize_answer
from app.answer_extraction.document_model import DocumentModel, DocumentTable
from app.answer_extraction.text_normalizer import normalize_text


@dataclass(frozen=True)
class StudentGridDetection:
    is_student_answer_grid: bool
    confidence: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "is_student_answer_grid": self.is_student_answer_grid,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
        }


def _row_values(table: DocumentTable, row_index: int) -> list[str]:
    grid = table.grid()
    if row_index >= len(grid):
        return []
    return [normalize_text(value) for value in grid[row_index]]


def detect_student_answer_grid(table: DocumentTable, document: DocumentModel | None = None) -> StudentGridDetection:
    grid = table.grid()
    joined = "\n".join(" ".join(row) for row in grid)
    normalized = normalize_text(joined)
    has_q = "题号" in normalized
    has_a = "答案" in normalized
    reasons: list[str] = []
    if has_q and has_a:
        reasons.append("has question and answer labels")
    answer_rows = [i for i, row in enumerate(grid) if any("答案" in normalize_text(cell) for cell in row)]
    answer_values: list[str] = []
    for row_index in answer_rows:
        values = _row_values(table, row_index)[1:]
        answer_values.extend(values)
    non_empty = [value for value in answer_values if value]
    valid_answers = [value for value in non_empty if normalize_answer(value).is_valid]
    if not non_empty:
        reasons.append("empty answer row")
    if table.order_index <= 3:
        reasons.append("early document position")
    if document:
        prefix = "\n".join(block.text for block in document.sorted_blocks()[:5])
        suffix = "\n".join(block.text for block in document.sorted_blocks()[table.order_index + 1 :])
        if any(token in prefix for token in ("班级", "姓名", "评分", "考号")):
            reasons.append("near class/name fields")
        if any(token in suffix for token in ("一、", "单选", "1.", "1．", "1、")):
            reasons.append("followed by question region")
    is_grid = has_q and has_a and not valid_answers and ("empty answer row" in reasons)
    if is_grid and ("early document position" in reasons or "near class/name fields" in reasons):
        confidence = 0.99
    elif is_grid:
        confidence = 0.85
    else:
        confidence = 0.1
    return StudentGridDetection(is_grid, confidence, reasons)
