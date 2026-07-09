from __future__ import annotations

from dataclasses import dataclass

from app.answer_extraction.document_model import DocumentTable
from app.answer_extraction.text_normalizer import normalize_text


@dataclass(frozen=True)
class NormalizedTable:
    table_id: str
    rows: list[list[str]]

    def is_empty_row(self, index: int) -> bool:
        return index < 0 or index >= len(self.rows) or all(not cell for cell in self.rows[index])

    def row_has_label(self, index: int, label: str) -> bool:
        return 0 <= index < len(self.rows) and any(label in cell for cell in self.rows[index])

    def row_pair_indexes(self) -> list[tuple[int, int]]:
        pairs: list[tuple[int, int]] = []
        for index in range(len(self.rows) - 1):
            if self.row_has_label(index, "题号") and self.row_has_label(index + 1, "答案"):
                pairs.append((index, index + 1))
        return pairs

    def vertical_columns(self) -> tuple[int, int] | None:
        if not self.rows:
            return None
        header = self.rows[0]
        if "题号" in header and "答案" in header:
            return header.index("题号"), header.index("答案")
        return None


def normalize_table(table: DocumentTable) -> NormalizedTable:
    grid = table.grid()
    width = max((len(row) for row in grid), default=0)
    rows: list[list[str]] = []
    for row in grid:
        normalized = [normalize_text(cell) for cell in row]
        normalized.extend([""] * (width - len(normalized)))
        if any(cell for cell in normalized):
            rows.append(normalized)
    return NormalizedTable(table.table_id, rows)


def answer_row_empty_ratio(row: list[str]) -> float:
    values = row[1:] if len(row) > 1 else row
    if not values:
        return 1.0
    empty = sum(1 for value in values if not value)
    return empty / len(values)
