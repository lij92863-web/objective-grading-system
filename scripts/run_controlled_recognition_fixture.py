#!/usr/bin/env python3
"""Controlled recognition fixture runner — dry-run only, no real API."""
import argparse, json, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True); p.add_argument("--layout", required=True)
    p.add_argument("--payload-dir", required=True); p.add_argument("--out-dir", required=True)
    p.add_argument("--dry-run", action="store_true", default=True)
    args = p.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.recognition.controlled_runner import run_controlled_recognition
    try:
        result = run_controlled_recognition(args.image, args.layout, args.payload_dir, args.out_dir, dry_run=True)
        summary_path = Path(args.out_dir) / "recognition_summary.json"
        if not summary_path.exists():
            print("FAILED: no summary generated", file=sys.stderr); return 1
        print(json.dumps(result.summary, indent=2))
        return 0
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr); return 1

if __name__ == "__main__":
    raise SystemExit(main())
