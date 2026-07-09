#!/usr/bin/env python3
"""R152: Recognition state snapshot synthetic CLI."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.batch_orchestrator import run_synthetic_batch
from app.recognition.state_snapshot import RecognitionStateSnapshot


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="with_review")
    args = p.parse_args()
    batch = run_synthetic_batch(args.scenario)
    snapshot = RecognitionStateSnapshot(snapshot_id="snap-001", batch_id=batch["job_id"],
                                         status=batch["status"], review_summary=batch["review_queue_summary"],
                                         qwen_policy_summary=batch["qwen_cost"])
    print(json.dumps(snapshot.to_safe_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
