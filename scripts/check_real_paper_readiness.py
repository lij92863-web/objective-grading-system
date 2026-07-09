#!/usr/bin/env python3
"""Real paper readiness CLI v2."""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.real_paper_readiness_gate import check_readiness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--has-anonymous-image", action="store_true")
    parser.add_argument("--has-template", action="store_true")
    parser.add_argument("--has-manual-roi", action="store_true")
    parser.add_argument("--qwen-check-only-passed", action="store_true")
    parser.add_argument("--qwen-api-key-present", action="store_true")
    args = parser.parse_args()
    result = check_readiness(
        has_anonymous_image=args.has_anonymous_image,
        has_template=args.has_template,
        has_manual_roi=args.has_manual_roi,
        qwen_check_only_passed=args.qwen_check_only_passed,
        qwen_api_key_present=args.qwen_api_key_present,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
