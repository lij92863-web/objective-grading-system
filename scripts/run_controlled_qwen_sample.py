#!/usr/bin/env python3
"""R22: Controlled Qwen sample CLI — fail-closed by default."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    p = argparse.ArgumentParser(description="Controlled single Qwen sample — default DISABLED")
    p.add_argument("--image", default="")
    p.add_argument("--allow-real-api", action="store_true")
    p.add_argument("--api-key-env", default="QWEN_API_KEY")
    p.add_argument("--output", default="")
    p.add_argument("--dry-run", action="store_true", default=True)
    args = p.parse_args()

    if not args.allow_real_api:
        result = {"status": "disabled", "error": "Real API disabled; pass --allow-real-api explicitly"}
        print(json.dumps(result, indent=2))
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(result, indent=2), "utf-8")
        return 1

    if not args.image:
        result = {"status": "blocked", "error": "No image path provided"}
        print(json.dumps(result, indent=2))
        return 1

    import os
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        result = {"status": "blocked", "error": f"API key env var '{args.api_key_env}' not set"}
        print(json.dumps(result, indent=2))
        return 1

    result = {"status": "not_executed",
              "error": "Real Qwen endpoint not configured — cannot make actual API call",
              "image": Path(args.image).name, "allow_real_api": True}
    print(json.dumps(result, indent=2))
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2), "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
