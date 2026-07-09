#!/usr/bin/env python3
"""Evaluate synthetic batch fixtures by comparing actual output to expected."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.recognition.batch_orchestrator import run_synthetic_batch
from app.recognition.synthetic_batch_loader import load_all_fixtures, load_fixture_by_path, load_fixture_by_scenario


def _actual_projection(result: dict) -> dict:
    summary = result["batch_summary"]
    statuses = result["student_statuses"]
    return {
        "batch_status": result["status"],
        "total_students": result["images"],
        "total_items": result["total_items"],
        "auto_accepted_items": summary["auto_accepted_items"],
        "needs_review_items": summary["needs_review_items"],
        "blocking_items": summary["blocking_items"],
        "qwen_call_count": summary["qwen_call_count"],
        "blocked_by_budget_count": summary["blocked_by_budget_count"],
        "ready_students": sum(1 for value in statuses.values() if value == "ready"),
        "needs_review_students": sum(1 for value in statuses.values() if value == "needs_review"),
        "blocked_students": sum(1 for value in statuses.values() if value == "blocked"),
    }


def evaluate_loaded_fixture(fixture, fixture_path: str | None = None) -> dict:
    if fixture_path:
        result = run_synthetic_batch(fixture_path=fixture_path)
    else:
        result = run_synthetic_batch(scenario=fixture.scenario)
    actual = _actual_projection(result)
    expected = fixture.expected
    mismatches = {
        key: {"expected": expected.get(key), "actual": actual.get(key)}
        for key in expected
        if expected.get(key) != actual.get(key)
    }
    return {
        "fixture": fixture.batch_id,
        "scenario": fixture.scenario,
        "passed": not mismatches,
        "expected": expected,
        "actual": actual,
        "mismatches": mismatches,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="")
    parser.add_argument("--scenario", default="")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    try:
        if args.all:
            results = [evaluate_loaded_fixture(fixture) for fixture in load_all_fixtures()]
        elif args.fixture:
            fixture = load_fixture_by_path(args.fixture)
            results = [evaluate_loaded_fixture(fixture, args.fixture)]
        elif args.scenario:
            fixture = load_fixture_by_scenario(args.scenario)
            results = [evaluate_loaded_fixture(fixture)]
        else:
            fixture = load_fixture_by_scenario("all_clear")
            results = [evaluate_loaded_fixture(fixture)]
    except ValueError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2
    output = {
        "total": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if output["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
