#!/usr/bin/env python3
"""Validate a single-image manifest without external effects."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.single_image_manifest import load_single_image_manifest, validate_single_image_manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_single_image_manifest(load_single_image_manifest(args.manifest))
    except Exception as exc:
        result = {"valid": False, "warnings": [], "blockers": [f"LOAD_FAILED:{exc}"], "manifest_summary": {}}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
