from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.answer_extraction.answer_layout_classifier import classify_answer_layout
from app.answer_extraction.extraction_engine import load_document
from app.answer_extraction.file_role_classifier import classify_file_role
from app.answer_extraction.student_answer_grid_detector import detect_student_answer_grid


def _classify(path: str) -> dict[str, object]:
    document = load_document(path)
    role = classify_file_role(document)
    layout = classify_answer_layout(document)
    grids = [table.table_id for table in document.sorted_tables() if detect_student_answer_grid(table, document).is_student_answer_grid]
    return {
        "file": Path(path).name,
        "file_role": role.role.value,
        "answer_layout": layout.layout.value,
        "detected_tables": layout.to_dict()["table_semantics"],
        "student_answer_grids": grids,
        "confidence": min(role.confidence, layout.confidence),
        "reasons": role.reasons + layout.reasons,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify teacher paper files for answer extraction.")
    parser.add_argument("--file")
    parser.add_argument("--question")
    parser.add_argument("--answer")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    paths = [path for path in [args.file, args.question, args.answer] if path]
    if not paths:
        parser.error("use --file or --question/--answer")
    result = {"files": [_classify(path) for path in paths]}
    if len(result["files"]) == 1:
        result.update(result["files"][0])
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
