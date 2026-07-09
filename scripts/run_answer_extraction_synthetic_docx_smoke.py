from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.answer_extraction.extraction_engine import extract_answer_key
from scripts.generate_answer_extraction_synthetic_docx import OUT_DIR, generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    generate()
    runs = []
    for docx in sorted(OUT_DIR.glob("*.docx")):
        try:
            result = extract_answer_key([str(docx)]).to_safe_dict()
            runs.append({
                "case_id": docx.stem,
                "detected_strategy": result["strategy"],
                "status": result["status"],
                "question_count": result["question_count"],
                "answer_count": result["answer_count"],
                "missing_answers": result["missing_answers"],
                "blocking_errors": result["blocking_errors"],
                "review_items": result["review_items"],
                "evidence_sample": list(result.get("evidence_summary", {}).values())[:2],
            })
        except Exception as exc:
            runs.append({"case_id": docx.stem, "status": "failed", "error": str(exc)})
    output = {"status": "completed", "case_count": len(runs), "runs": runs}
    print(json.dumps(output, ensure_ascii=False, indent=2) if args.as_json else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
