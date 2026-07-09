from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.answer_extraction.document_model import DocumentModel


class DocumentModelLoadError(ValueError):
    pass


@dataclass(frozen=True)
class DocumentModelLoadResult:
    document: DocumentModel
    warnings: list[str] = field(default_factory=list)


def validate_document_model_data(data: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not data.get("document_id"):
        raise DocumentModelLoadError("document_id is required")
    blocks = data.get("blocks")
    if not isinstance(blocks, list):
        raise DocumentModelLoadError("blocks must be a list")
    seen: set[str] = set()
    for block in blocks:
        block_id = block.get("block_id")
        if not block_id:
            raise DocumentModelLoadError("block_id is required")
        if block_id in seen:
            raise DocumentModelLoadError(f"duplicate block_id: {block_id}")
        seen.add(block_id)
        if "order_index" not in block:
            raise DocumentModelLoadError(f"missing order_index: {block_id}")
        if block.get("block_type", "paragraph") == "paragraph" and not block.get("text"):
            warnings.append(f"empty paragraph: {block_id}")
    for table in data.get("tables", []):
        if not table.get("table_id"):
            raise DocumentModelLoadError("table_id is required")
        if not isinstance(table.get("cells"), list) or not table.get("cells"):
            raise DocumentModelLoadError(f"table without cells: {table.get('table_id')}")
        for cell in table["cells"]:
            if "row_index" not in cell or "col_index" not in cell:
                raise DocumentModelLoadError(f"invalid table cell: {table.get('table_id')}")
    return warnings


def load_document_model_json(path: str | Path) -> DocumentModelLoadResult:
    file_path = Path(path)
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DocumentModelLoadError("invalid JSON document model") from exc
    warnings = validate_document_model_data(data)
    document = DocumentModel.from_dict(data)
    document.blocks = document.sorted_blocks()
    document.tables = document.sorted_tables()
    if not document.source_file:
        document.source_file = file_path.name
    for block in document.blocks:
        if not block.source_file:
            block.source_file = document.source_file
    for table in document.tables:
        if not table.source_file:
            table.source_file = document.source_file
    return DocumentModelLoadResult(document, warnings)
