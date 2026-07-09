from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.answer_extraction.extraction_engine import extract_answer_key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract a teacher answer key from synthetic DocumentModel JSON or DOCX.")
    parser.add_argument("--file")
    parser.add_argument("--question")
    parser.add_argument("--answer")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allow-review-status", action="store_true")
    parser.add_argument("--show-evidence", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args(argv)
    files: list[str] = []
    if args.file:
        files.append(args.file)
    elif args.question and args.answer:
        files.extend([args.question, args.answer])
    else:
        parser.error("use --file or --question plus --answer")
    try:
        result = extract_answer_key(files).to_safe_dict()
        if args.summary_only:
            result = {key: result[key] for key in ("strategy", "status", "question_count", "answer_count", "missing_answers", "blocking_errors", "review_items")}
        if not args.show_evidence and "answers" in result:
            for answer in result["answers"].values():
                answer.pop("evidence_text", None)
    except Exception as exc:
        result = {"status": "failed", "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)
    if args.strict and result["status"] not in {"accepted", "accepted_with_warnings"}:
        return 1
    return 1 if result["status"] in {"failed"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
