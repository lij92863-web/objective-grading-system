#!/usr/bin/env python3
"""Run the single-image dry-run contract pipeline."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.single_image_dry_run import run_single_image_dry_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--roi", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_single_image_dry_run(args.manifest, args.roi)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
