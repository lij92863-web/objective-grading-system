from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.answer_extraction.extraction_engine import extract_answer_key


SAMPLE_DIR = ROOT / "local-test-materials" / "answer-extraction-samples"
CASES = [
    ("case1_type2_itemized", ["基础训练13(1).docx"]),
    ("case2_type4_split_itemized", ["高一数学基础训练16.docx", "高一数学基础训练16答案.docx"]),
    ("case3_type1_same_file_boxed", ["2026年5月8日高中数学作业(1).docx"]),
    ("case4_type3_split_boxed", ["题目(1).docx", "答案(1).docx"]),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local-only answer extraction smoke tests.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    if not SAMPLE_DIR.exists():
        result = {"status": "skipped", "reason": "local samples missing", "sample_dir": str(SAMPLE_DIR.relative_to(ROOT))}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result)
        return 0
    runs = []
    for case_id, names in CASES:
        paths = [SAMPLE_DIR / name for name in names]
        missing = [path.name for path in paths if not path.exists()]
        if missing:
            runs.append({"case_id": case_id, "files": names, "status": "skipped", "missing_files": missing})
            continue
        try:
            extracted = extract_answer_key([str(path) for path in paths]).to_safe_dict()
            runs.append({
                "case_id": case_id,
                "files": names,
                "detected_strategy": extracted["strategy"],
                "status": extracted["status"],
                "question_count": extracted["question_count"],
                "answer_count": extracted["answer_count"],
                "missing_answers": extracted["missing_answers"],
                "blocking_errors": extracted["blocking_errors"],
                "review_items": extracted["review_items"],
            })
        except Exception as exc:
            runs.append({"case_id": case_id, "files": names, "status": "failed", "error": str(exc)})
    result = {"status": "completed", "runs": runs}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
