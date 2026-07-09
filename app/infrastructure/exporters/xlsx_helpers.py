"""Standard-library XLSX helper — zero external dependencies.

Mirrors the behaviour of ``legacy.write_xlsx``: writes Open XML
Spreadsheet (.xlsx) files using only ``zipfile`` + ``xml.sax.saxutils``.

Usage::

    from app.infrastructure.exporters.xlsx_helpers import XlsxSheet, write_xlsx

    write_xlsx(
        Path("out.xlsx"),
        [XlsxSheet(name="成绩", rows=[["姓名","分数"],["张三","95"]])],
    )

Design principles (from E3A-H audit, Route B):
- **inlineStr only** — no sharedStrings, matching the legacy pure-Python path
- **no styles.xml** — plain output (styles require openpyxl, which is optional)
- **no formulas, no column widths, no freeze panes**
- **ZIP_DEFLATED** compression
- **sheet names truncated to 31 chars** (Excel limit)
"""

import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List, Union
from xml.sax.saxutils import escape as xml_escape


# ── data types ────────────────────────────────────────────────────────────

@dataclass
class XlsxSheet:
    """One worksheet inside an xlsx workbook.

    Attributes
    ----------
    name:
        Sheet display name (max 31 chars, will be truncated if longer).
    rows:
        List of rows; each row is a list of cell values (converted to ``str``).
    """
    name: str
    rows: List[List[Any]] = field(default_factory=list)


# ── internal helpers ─────────────────────────────────────────────────────

def _excel_column_name(index: int) -> str:
    """Convert 1-based column index → Excel column letter(s).  1→A, 27→AA."""
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _xml_attr(value: str) -> str:
    """Escape a value for use in an XML attribute (double-quoted)."""
    return xml_escape(value, {'"': "&quot;"})


def _worksheet_xml(rows: List[List[Any]]) -> str:
    """Build an OOXML worksheet XML string with inlineStr cells."""
    xml_rows: List[str] = []
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    for row_index, row in enumerate(rows, start=1):
        cells: List[str] = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{_excel_column_name(col_index)}{row_index}"
            text = xml_escape(str(value))
            cells.append(
                f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>'
            )
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet {ns}>'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


# ── public API ────────────────────────────────────────────────────────────

def write_xlsx(path: Path, sheets: List[XlsxSheet]) -> Path:
    """Write an .xlsx workbook to *path* using only the standard library.

    Parameters
    ----------
    path:
        Output file path (parent directories are created if needed).
    sheets:
        Ordered list of sheets.  Each sheet name is truncated to 31 chars
        (Excel maximum).  Empty sheets get a single ``"empty"`` cell row
        so the workbook remains valid.

    Returns
    -------
    Path:
        The *path* that was written (for chaining).

    Raises
    ------
    OSError:
        If the file cannot be written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Normalise: truncate sheet names, ensure non-empty rows
    safe_sheets: List[XlsxSheet] = [
        XlsxSheet(
            name=sheet.name[:31],
            rows=sheet.rows if sheet.rows else [["empty"]],
        )
        for sheet in sheets
    ]

    # -- build workbook XML fragments --------------------------------------
    workbook_sheets: List[str] = []
    workbook_rels: List[str] = []
    content_overrides = [
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.sheet.main+xml"/>',
    ]

    for index, sheet in enumerate(safe_sheets, start=1):
        workbook_sheets.append(
            f'<sheet name="{_xml_attr(sheet.name)}" '
            f'sheetId="{index}" r:id="rId{index}"/>'
        )
        workbook_rels.append(
            f'<Relationship Id="rId{index}" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            f'relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        )
        content_overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
            f'ContentType="application/vnd.openxmlformats-officedocument.'
            f'spreadsheetml.worksheet+xml"/>'
        )

    # -- assemble XML strings ----------------------------------------------
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + "".join(content_overrides)
        + "</Types>"
    )

    root_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(workbook_sheets)}</sheets>'
        "</workbook>"
    )

    wb_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(workbook_rels)
        + "</Relationships>"
    )

    # -- write ZIP ---------------------------------------------------------
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", wb_rels_xml)
        for index, sheet in enumerate(safe_sheets, start=1):
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                _worksheet_xml(sheet.rows),
            )

    return path
