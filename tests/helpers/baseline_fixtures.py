"""Baseline fixture helpers — NO legacy import."""
import csv
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List

FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "baseline"
NS_S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_NS = {"ns": NS_S}


def load_json_fixture(name: str) -> Any:
    """Load a JSON baseline fixture."""
    path = FIXTURES_ROOT / "json" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv_fixture(name: str) -> List[Dict[str, str]]:
    """Load a CSV baseline fixture as list of dicts."""
    path = FIXTURES_ROOT / "csv" / f"{name}.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def normalize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Normalize rows for comparison: all values → str, sorted keys."""
    return [{k: str(v) for k, v in sorted(r.items())} for r in rows]


def normalize_html_structure(html: str) -> dict:
    """Extract structural summary from HTML."""
    import re
    title = re.search(r"<title>(.*?)</title>", html)
    sections = re.findall(r"<h[12]>(.*?)</h[12]>", html)
    links = re.findall(r'href="([^"]+)"', html)
    has_table = "<table" in html
    return {
        "title": title.group(1) if title else "",
        "sections": sections,
        "links": links,
        "has_table": has_table,
    }


def normalize_xlsx_structure(path: Path) -> dict:
    """Extract structural summary from XLSX without openpyxl."""
    with zipfile.ZipFile(path) as z:
        wb_xml = z.read("xl/workbook.xml").decode("utf-8")
        root = ET.fromstring(wb_xml)
        sheet_names = [s.get("name", "")
                       for s in root.findall(".//ns:sheet", NS_NS)]
        headers = {}
        for idx, name in enumerate(sheet_names, start=1):
            sp = f"xl/worksheets/sheet{idx}.xml"
            try:
                sx = z.read(sp).decode("utf-8")
            except KeyError:
                headers[name] = []
                continue
            sroot = ET.fromstring(sx)
            rows = sroot.findall(".//ns:row", NS_NS)
            if not rows:
                headers[name] = []
                continue
            cells = rows[0].findall(".//ns:c", NS_NS)
            hdr = []
            for cell in cells:
                is_e = cell.find(".//ns:is", NS_NS)
                if is_e is not None:
                    t_e = is_e.find("ns:t", NS_NS)
                    if t_e is not None and t_e.text is not None:
                        hdr.append(t_e.text)
            headers[name] = hdr
        return {
            "filename": path.name,
            "sheet_names": sheet_names,
            "sheet_count": len(sheet_names),
            "headers": headers,
            "file_size": path.stat().st_size,
        }


def assert_rows_match_fixture(actual_rows, fixture_name):
    """Compare actual rows to a JSON fixture."""
    expected = load_json_fixture(fixture_name)
    actual_norm = normalize_rows(actual_rows)
    assert actual_norm == expected, (
        f"Rows mismatch for {fixture_name}")
