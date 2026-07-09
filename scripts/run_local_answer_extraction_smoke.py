from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from fnmatch import fnmatch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.answer_extraction.extraction_engine import extract_answer_key


SAMPLE_DIR = ROOT / "local-test-materials" / "answer-extraction-samples"
CASES = [
    ("case1_type2_itemized_training13", ["基础训练13(1).docx"], ["*基础训练13*.docx"]),
    ("case2_split_itemized_training16", ["高一数学基础训练16.docx", "高一数学基础训练16答案.docx"], ["*基础训练16*.docx", "*基础训练16*答案*.docx"]),
    ("case3_same_file_boxed_2026", ["2026年5月8日高中数学作业(1).docx"], ["*2026*作业*.docx"]),
    ("case4_split_boxed_question_answer", ["题目(1).docx", "答案(1).docx"], ["题目*.docx", "答案*.docx"]),
]


def _resolve_case_files(names: list[str], patterns: list[str]) -> tuple[list[Path], list[str]]:
    resolved: list[Path] = []
    missing: list[str] = []
    all_docx = list(SAMPLE_DIR.glob("*.docx"))
    for name, pattern in zip(names, patterns):
        exact = SAMPLE_DIR / name
        if exact.exists():
            resolved.append(exact)
            continue
        fuzzy = next((path for path in all_docx if fnmatch(path.name, pattern)), None)
        if fuzzy:
            resolved.append(fuzzy)
        else:
            missing.append(name)
    return resolved, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local-only answer extraction smoke tests.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    if not SAMPLE_DIR.exists():
        result = {"status": "skipped", "reason": "local samples missing", "sample_dir": str(SAMPLE_DIR.relative_to(ROOT))}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result)
        return 0
    runs = []
    strict_failed = False
    for case_id, names, patterns in CASES:
        paths, missing = _resolve_case_files(names, patterns)
        if missing:
            runs.append({"case_id": case_id, "files": names, "status": "skipped", "missing_files": missing})
            continue
        try:
            extracted = extract_answer_key([str(path) for path in paths]).to_safe_dict()
            strict_failed = strict_failed or bool(extracted["blocking_errors"])
            runs.append({
                "case_id": case_id,
                "files": [path.name for path in paths],
                "detected_strategy": extracted["strategy"],
                "status": extracted["status"],
                "question_count": extracted["question_count"],
                "answer_count": extracted["answer_count"],
                "accepted_count": extracted["accepted_count"],
                "review_count": extracted["review_count"],
                "missing_answers": extracted["missing_answers"],
                "unexpected_answers": extracted["unexpected_answers"],
                "blocking_errors": extracted["blocking_errors"],
                "warnings": extracted["warnings"],
                "review_items": extracted["review_items"],
                "evidence_sample": list(extracted.get("evidence_summary", {}).values())[:2],
            })
        except Exception as exc:
            strict_failed = True
            runs.append({"case_id": case_id, "files": names, "status": "failed", "error": str(exc)})
    result = {"status": "completed", "runs": runs}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result)
    return 1 if args.strict and strict_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
