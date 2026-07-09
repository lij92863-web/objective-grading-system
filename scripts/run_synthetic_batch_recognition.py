#!/usr/bin/env python3
"""R91A: Synthetic batch recognition CLI — scenario-driven."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.batch_orchestrator import run_synthetic_batch


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="all_clear", choices=["all_clear","with_review","with_blocking_identity","qwen_budget_exceeded"])
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--json", action="store_true", default=True)
    args = p.parse_args()
    result = run_synthetic_batch(scenario=args.scenario, count=args.count)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
