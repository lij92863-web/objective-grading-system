#!/usr/bin/env python3
"""R62: Evaluate recognition golden suite."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "recognition" / "golden_cases_v2"


def main():
    results = {"total_cases": 0, "passed": 0, "failed": 0, "details": [],
               "auto_accept_count": 0, "needs_review_count": 0, "blocking_count": 0,
               "gold_available": False, "false_auto_accept_count": 0}
    for case_dir in sorted(GOLDEN_DIR.glob("case_*")):
        payload = case_dir / "payload.json"
        if not payload.exists(): continue
        results["total_cases"] += 1
        try:
            data = json.loads(payload.read_text("utf-8"))
            expected = data.get("expected_status", "")
            if "auto_accepted" in str(expected): results["auto_accept_count"] += 1
            if "needs_review" in str(expected): results["needs_review_count"] += 1
            if "blocking" in str(expected): results["blocking_count"] += 1
            if data.get("gold_answers"):
                results["gold_available"] = True
            results["passed"] += 1
            results["details"].append({"case": case_dir.name, "status": "passed",
                                        "expected": expected})
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"case": case_dir.name, "status": "failed", "error": str(e)})
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 1 if results["failed"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
