from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from app.answer_extraction.document_model import DocumentCell, DocumentModel, DocumentTable, ParagraphBlock, TableBlock
from app.answer_extraction.text_normalizer import normalize_text

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class DocxParseError(ValueError):
    pass


def _texts(element: ET.Element) -> str:
    parts: list[str] = []
    for node in element.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "t":
            parts.append(node.text or "")
        elif tag == "tab":
            parts.append("\t")
        elif tag == "br":
            parts.append("\n")
        elif tag in {"drawing", "object", "pict"}:
            parts.append("[object]")
        elif tag == "oMath":
            parts.append("[equation]")
    return "".join(parts)


def parse_docx(path: str | Path) -> DocumentModel:
    docx_path = Path(path)
    if not docx_path.exists():
        raise DocxParseError("docx file does not exist")
    if docx_path.suffix.lower() != ".docx":
        raise DocxParseError("not a docx file")
    try:
        with zipfile.ZipFile(docx_path) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise DocxParseError("invalid docx document") from exc
    root = ET.fromstring(xml_bytes)
    body = root.find("w:body", NS)
    if body is None:
        raise DocxParseError("docx body missing")
    blocks = []
    tables = []
    order = 0
    for child in list(body):
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = normalize_text(_texts(child))
            if text:
                blocks.append(ParagraphBlock(block_id=f"p_{order:03d}", text=text, raw_text=text, order_index=order, source_file=docx_path.name))
                order += 1
        elif tag == "tbl":
            rows = child.findall(".//w:tr", NS)
            cells: list[DocumentCell] = []
            col_count = 0
            for row_index, row in enumerate(rows):
                row_cells = row.findall("./w:tc", NS)
                col_count = max(col_count, len(row_cells))
                for col_index, cell in enumerate(row_cells):
                    paragraphs = [normalize_text(_texts(p)) for p in cell.findall("./w:p", NS)]
                    text = normalize_text("\n".join(part for part in paragraphs if part) or _texts(cell))
                    cells.append(DocumentCell(row_index, col_index, text=text, raw_text=text))
            table = DocumentTable(f"t_{len(tables):03d}", cells, len(rows), col_count, order_index=order, source_file=docx_path.name)
            tables.append(table)
            blocks.append(TableBlock.from_table(table, block_id=f"tb_{order:03d}"))
            order += 1
    return DocumentModel(document_id=docx_path.stem, source_file=docx_path.name, blocks=blocks, tables=tables)
