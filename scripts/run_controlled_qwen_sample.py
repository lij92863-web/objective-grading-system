#!/usr/bin/env python3
"""Controlled Qwen sample CLI: fail closed by default."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description="Controlled single Qwen sample, default disabled")
    parser.add_argument("--image", default="")
    parser.add_argument("--allow-real-api", action="store_true")
    parser.add_argument("--api-key-env", default="QWEN_API_KEY")
    parser.add_argument("--output", default="")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if args.check_only:
        print(json.dumps({"status": "check_only", "real_api_called": False, "ready": False}, indent=2))
        return 0

    if not args.allow_real_api:
        result = {"status": "disabled", "error": "Real API disabled; pass --allow-real-api explicitly"}
        print(json.dumps(result, indent=2))
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(result, indent=2), "utf-8")
        return 1

    if not args.image:
        print(json.dumps({"status": "blocked", "error": "No image path provided"}, indent=2))
        return 1

    import os
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        print(json.dumps({"status": "blocked", "error": f"API key env var '{args.api_key_env}' not set"}, indent=2))
        return 1

    result = {
        "status": "not_executed",
        "error": "Real Qwen endpoint not configured; cannot make actual API call",
        "image": Path(args.image).name,
        "allow_real_api": True,
    }
    print(json.dumps(result, indent=2))
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2), "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
