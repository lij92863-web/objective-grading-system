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
    except Exception as exc:
        result = {"status": "failed", "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)
    return 1 if result["status"] in {"failed"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
