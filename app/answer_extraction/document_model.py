from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceSpan:
    start_block: str = ""
    end_block: str = ""
    table_id: str = ""
    page_index: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SourceSpan":
        return cls(**(data or {}))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentCell:
    row_index: int
    col_index: int
    text: str = ""
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentCell":
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentTable:
    table_id: str
    cells: list[DocumentCell] = field(default_factory=list)
    row_count: int = 0
    col_count: int = 0
    page_index: int = 0
    order_index: int = 0
    source_file: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentTable":
        data = dict(data)
        data["cells"] = [DocumentCell.from_dict(cell) for cell in data.get("cells", [])]
        if not data.get("row_count"):
            data["row_count"] = 1 + max((c.row_index for c in data["cells"]), default=-1)
        if not data.get("col_count"):
            data["col_count"] = 1 + max((c.col_index for c in data["cells"]), default=-1)
        return cls(**data)

    def grid(self) -> list[list[str]]:
        rows = [["" for _ in range(self.col_count)] for _ in range(self.row_count)]
        for cell in self.cells:
            if 0 <= cell.row_index < self.row_count and 0 <= cell.col_index < self.col_count:
                rows[cell.row_index][cell.col_index] = cell.text
        return rows

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentBlock:
    block_id: str
    block_type: str
    text: str = ""
    raw_text: str = ""
    page_index: int = 0
    order_index: int = 0
    source_file: str = ""
    style: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentBlock":
        kind = data.get("block_type", "paragraph")
        block_cls = {
            "paragraph": ParagraphBlock,
            "table": TableBlock,
            "image": ImageBlock,
            "equation": EquationBlock,
        }.get(kind, DocumentBlock)
        data = dict(data)
        if block_cls is TableBlock and isinstance(data.get("table"), dict):
            data["table"] = DocumentTable.from_dict(data["table"])
        return block_cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParagraphBlock(DocumentBlock):
    block_type: str = "paragraph"


@dataclass
class TableBlock(DocumentBlock):
    block_type: str = "table"
    table_id: str = ""
    table: DocumentTable | None = None

    @classmethod
    def from_table(cls, table: DocumentTable, block_id: str | None = None, text: str = "") -> "TableBlock":
        return cls(
            block_id=block_id or f"tb_{table.table_id}",
            text=text or "\n".join(" | ".join(row) for row in table.grid()),
            raw_text=text or "\n".join(" | ".join(row) for row in table.grid()),
            page_index=table.page_index,
            order_index=table.order_index,
            source_file=table.source_file,
            table_id=table.table_id,
            table=table,
        )


@dataclass
class ImageBlock(DocumentBlock):
    block_type: str = "image"


@dataclass
class EquationBlock(DocumentBlock):
    block_type: str = "equation"


@dataclass
class DocumentModel:
    document_id: str
    source_file: str = ""
    blocks: list[DocumentBlock] = field(default_factory=list)
    tables: list[DocumentTable] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def sorted_blocks(self) -> list[DocumentBlock]:
        return sorted(self.blocks, key=lambda b: (b.page_index, b.order_index, b.block_id))

    def sorted_tables(self) -> list[DocumentTable]:
        return sorted(self.tables, key=lambda t: (t.page_index, t.order_index, t.table_id))

    def all_text(self) -> str:
        return "\n".join(block.text for block in self.sorted_blocks() if block.text)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentModel":
        data = dict(data)
        tables = [DocumentTable.from_dict(table) for table in data.get("tables", [])]
        data["tables"] = tables
        data["blocks"] = [DocumentBlock.from_dict(block) for block in data.get("blocks", [])]
        by_id = {table.table_id: table for table in tables}
        for block in data["blocks"]:
            if isinstance(block, TableBlock) and block.table is None and block.table_id in by_id:
                block.table = by_id[block.table_id]
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "source_file": self.source_file,
            "blocks": [block.to_dict() for block in self.sorted_blocks()],
            "tables": [table.to_dict() for table in self.sorted_tables()],
            "metadata": dict(self.metadata),
        }
