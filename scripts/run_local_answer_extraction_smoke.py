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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local-only answer extraction smoke tests.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    if not SAMPLE_DIR.exists():
        result = {"status": "skipped", "reason": "local samples missing", "sample_dir": str(SAMPLE_DIR.relative_to(ROOT))}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result)
        return 0
    sample_files = sorted(str(path) for path in SAMPLE_DIR.glob("*.docx"))
    runs = []
    for sample in sample_files:
        try:
            runs.append(extract_answer_key([sample]).to_safe_dict())
        except Exception as exc:
            runs.append({"file": Path(sample).name, "status": "failed", "error": str(exc)})
    result = {"status": "completed", "runs": runs}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
