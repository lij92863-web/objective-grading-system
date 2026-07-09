#!/usr/bin/env python3
"""Controlled recognition fixture runner: dry-run only, no real API."""
import argparse
import json
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=str(root / "tests" / "fixtures" / "recognition" / "images" / "fake_answer_sheet.png"))
    parser.add_argument("--layout", default=str(root / "tests" / "fixtures" / "recognition" / "layouts" / "demo_layout.json"))
    parser.add_argument("--payload-dir", default=str(root / "tests" / "fixtures" / "recognition" / "fake_engine_payloads"))
    parser.add_argument("--out-dir", default=str(root / "data" / "tmp" / "controlled_recognition_dry_run"))
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()
    sys.path.insert(0, str(root))
    from app.recognition.controlled_runner import run_controlled_recognition

    try:
        result = run_controlled_recognition(args.image, args.layout, args.payload_dir, args.out_dir, dry_run=True)
        print(json.dumps(result.summary, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
