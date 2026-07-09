#!/usr/bin/env python3
"""Validate a manual ROI JSON file."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.manual_roi_schema import load_manual_roi_file, validate_manual_roi_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roi", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_manual_roi_file(load_manual_roi_file(args.roi))
    except Exception as exc:
        result = {"valid": False, "warnings": [], "blockers": [f"LOAD_FAILED:{exc}"], "roi_summary": {}}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
