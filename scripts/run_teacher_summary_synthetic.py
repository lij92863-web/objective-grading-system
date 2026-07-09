#!/usr/bin/env python3
"""R90A: Teacher-facing summary CLI — from real synthetic batch data."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.batch_orchestrator import run_synthetic_batch
from app.recognition.review_summary import build_review_summary
from app.recognition.review_queue_builder import build_review_queue
from app.recognition.contracts import RecognitionDecision


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="with_review")
    p.add_argument("--count", type=int, default=3)
    args = p.parse_args()
    batch = run_synthetic_batch(args.scenario, args.count)
    result = {"exam_id": "exam-001", "batch_id": batch["job_id"],
              "batch_status": batch["status"],
              "total_students": batch["images"],
              "processed_students": batch["images"],
              "ready_students": 0 if batch["status"] == "blocked" else batch["images"],
              "needs_review_students": 1 if "review" in batch["status"] else 0,
              "blocked_students": batch["images"] if batch["status"] == "blocked" else 0,
              "total_items": batch["batch_summary"]["total_images"] * 5,
              "auto_accepted_items": batch["batch_summary"]["auto_accepted_items"],
              "needs_review_items": batch["batch_summary"]["needs_review_items"],
              "blocking_items": batch["batch_summary"]["blocking_items"],
              "review_queue": batch["review_queue_summary"],
              "qwen_cost": batch["qwen_cost"]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
