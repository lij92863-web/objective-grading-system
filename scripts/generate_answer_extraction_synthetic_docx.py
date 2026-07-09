from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tests" / "fixtures" / "answer_extraction" / "synthetic_docx_v3"


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def p(text: str) -> str:
    if "\t" in text or "\n" in text:
        parts = []
        for piece in text.replace("\n", "<BR>").replace("\t", "<TAB>").split("<"):
            if piece.startswith("BR>"):
                parts.append("<w:br/>")
                piece = piece[3:]
            if piece.startswith("TAB>"):
                parts.append("<w:tab/>")
                piece = piece[4:]
            if piece:
                parts.append(f"<w:r><w:t>{_esc(piece)}</w:t></w:r>")
        return f"<w:p>{''.join(parts)}</w:p>"
    return f"<w:p><w:r><w:t>{_esc(text)}</w:t></w:r></w:p>"


def tbl(rows: list[list[str]]) -> str:
    row_xml = []
    for row in rows:
        cells = []
        for cell in row:
            paras = "".join(p(part) for part in cell.split("\n")) or p("")
            cells.append(f"<w:tc>{paras}</w:tc>")
        row_xml.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return f"<w:tbl>{''.join(row_xml)}</w:tbl>"


def make_docx(path: Path, parts: list[str]) -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(parts)}<w:p><w:r><w:drawing/></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        archive.writestr("word/document.xml", xml)


CASES = {
    "same_file_boxed_front_empty_grid.docx": {
        "parts": [p("班级 姓名 评分"), tbl([["题号", "1", "2"], ["答案", "", ""]]), p("一、单选题"), p("1. 题干 A.甲 B.乙 C.丙 D.丁"), p("2. 题干 A.甲 B.乙 C.丙 D.丁"), p("参考答案"), tbl([["题号", "1", "2"], ["答案", "B", "C"]])],
        "expected": {"strategy": "same_file_boxed", "answers": {"1": "B", "2": "C"}},
    },
    "same_file_itemized_real_brackets.docx": {
        "parts": [p("一、单选题"), p("1. 题干 A.甲 B.乙 C.丙 D.丁"), p("2. 题干 A.甲 B.乙 C.丙 D.丁"), p("答案解析"), p("1.【答案】B"), p("2．【答案】C")],
        "expected": {"strategy": "same_file_itemized", "answers": {"1": "B", "2": "C"}, "expected_evidence_contains": "【答案】"},
    },
    "split_question_with_empty_grid.docx": {
        "parts": [p("班级 姓名 评分"), tbl([["题号", "1", "2"], ["答案", "", ""]]), p("一、单选题"), p("1. 题干 A.甲 B.乙 C.丙 D.丁"), p("2. 题干 A.甲 B.乙 C.丙 D.丁")],
        "expected": {"strategy": "question_only_no_answer", "answers": {}},
    },
    "split_answer_boxed_segmented.docx": {
        "parts": [p("参考答案"), tbl([["题号", "1", "2"], ["答案", "B", "C"], ["题号", "3"], ["答案", "B D"]])],
        "expected": {"strategy": "answer_only_without_question", "answers": {"1": "B", "2": "C", "3": "BD"}},
    },
    "split_answer_itemized_real_brackets.docx": {
        "parts": [p("答案解析"), p("1."), p("【答案】B"), p("2．【答案】C")],
        "expected": {"strategy": "answer_only_without_question", "answers": {"1": "B", "2": "C"}, "expected_evidence_contains": "【答案】"},
    },
    "itemized_fill_blank_complex.docx": {
        "parts": [p("三、填空题"), p("12. 填空____"), p("13. 填空____"), p("参考答案"), p("12．【答案】\\frac{1}{2}"), p("13．【答案】[-1,2]")],
        "expected": {"strategy": "same_file_itemized", "answers": {"12": "\\frac{1}{2}", "13": "[-1,2]"}},
    },
    "boxed_vertical_table.docx": {
        "parts": [p("参考答案"), tbl([["题号", "答案"], ["1", "B"], ["2", "C"]])],
        "expected": {"strategy": "answer_only_without_question", "answers": {"1": "B", "2": "C"}},
    },
    "unknown_mixed_should_review.docx": {
        "parts": [p("课堂材料：答案一词只在题干中出现，没有标准答案。")],
        "expected": {"strategy": "mixed_or_unknown", "answers": {}},
    },
}


def generate() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for name, spec in CASES.items():
        path = OUT_DIR / name
        make_docx(path, spec["parts"])
        expected_path = OUT_DIR / f"{path.stem}.expected.json"
        expected_path.write_text(json.dumps(spec["expected"], ensure_ascii=False, indent=2), encoding="utf-8")
        generated.append({"file": str(path.relative_to(ROOT)), "expected": str(expected_path.relative_to(ROOT))})
    return {"status": "generated", "count": len(generated), "generated": generated}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = generate()
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
