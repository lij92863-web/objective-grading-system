#!/usr/bin/env python3
"""R66: Synthetic recognition dry-run."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "recognition"


def main():
    from app.recognition.contracts import RecognitionRunConfig, RecognitionRunResult
    from app.recognition.decision import fuse_candidates
    from app.recognition.evaluation_v2 import evaluate_recognition, EvaluationReport

    results = {"total_payloads": 0, "summary": {}}
    payload_dir = FIXTURES / "synthetic_payloads"
    for f in sorted(payload_dir.glob("*.json")):
        results["total_payloads"] += 1
        data = json.loads(f.read_text("utf-8"))
    report = EvaluationReport(total_items=results["total_payloads"],
                               gold_available=False,
                               warnings=["synthetic_dry_run_no_real_api"])
    results["summary"] = {"evaluation": str(report)}
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
