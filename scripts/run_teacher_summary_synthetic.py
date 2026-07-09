#!/usr/bin/env python3
"""Teacher-facing summary CLI from synthetic batch models."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.batch_orchestrator import run_synthetic_batch
from app.recognition.batch_summary import BatchRecognitionSummary
from app.recognition.teacher_facing_summary import TeacherFacingSummary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="with_review")
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--fixture", default="")
    args = parser.parse_args()
    batch = run_synthetic_batch(args.scenario, args.count, fixture_path=args.fixture or None)
    summary_model = BatchRecognitionSummary(**batch["batch_summary"])
    evaluation_summary = {"total_students": batch["images"], "total_items": batch["total_items"]}
    teacher_summary = TeacherFacingSummary.from_models(
        summary_model,
        batch["review_queue_summary"],
        evaluation_summary,
        batch["qwen_cost"],
        exam_id=batch["exam_id"],
        batch_id=batch["job_id"],
        student_statuses=batch["student_statuses"],
    )
    result = teacher_summary.to_safe_dict()
    result["batch_status"] = batch["status"]
    result["processed_students"] = teacher_summary.processed_students
    result["review_queue"] = batch["review_queue_summary"]
    result["qwen_cost"] = batch["qwen_cost"]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
