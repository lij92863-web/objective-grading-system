#!/usr/bin/env python3
"""Synthetic batch recognition CLI, fixture-driven."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.batch_orchestrator import run_synthetic_batch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="")
    parser.add_argument("--scenario", default="all_clear")
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()
    try:
        result = run_synthetic_batch(
            scenario=args.scenario,
            count=args.count,
            fixture_path=args.fixture or None,
        )
    except ValueError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
