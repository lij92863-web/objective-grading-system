#!/usr/bin/env python3
"""Write Not-Executed Report for single real Qwen trial.

Documents WHY real API was NOT called. real_api_called is ALWAYS false.
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_real_trial_not_executed_report import build_not_executed_report


def main():
    parser = argparse.ArgumentParser(description="Write Not-Executed Trial Report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", default="", help="Optional output path (data/tmp only)")
    parser.add_argument("--api-key-env", default="", help="Env var name to check (not value)")
    args = parser.parse_args()

    api_key_present = False
    if args.api_key_env:
        api_key_present = bool(os.environ.get(args.api_key_env, "").strip())

    report = build_not_executed_report(
        reason="Stage R361-R440: controlled single Qwen trial gate without calling real API",
        api_key_present=api_key_present,
        anonymous_confirmed=False,
        check_only_passed=False,
    )

    output_data = report.to_dict()

    if args.json:
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

    # Optionally write to file (data/tmp only)
    if args.output:
        output_path = Path(args.output)
        output_str = str(output_path).replace("\\", "/")
        if "data/tmp" not in output_str and "data\\tmp" not in str(output_path):
            print("Error: output must be in data/tmp", file=sys.stderr)
            sys.exit(1)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.json:
            print(f"Report written to: {output_path}")

    if not args.json and not args.output:
        print(f"Not-Executed Report:")
        print(f"  real_api_called: {report.real_api_called}")
        print(f"  reason: {report.reason}")
        print(f"  api_key_present: {report.api_key_present}")
        print(f"  missing prerequisites: {report.missing_prerequisites}")

    sys.exit(0)


if __name__ == "__main__":
    main()
