#!/usr/bin/env python3
"""Recognition state snapshot synthetic CLI."""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.batch_orchestrator import run_synthetic_batch
from app.recognition.batch_summary import BatchRecognitionSummary
from app.recognition.real_paper_readiness_gate import check_readiness
from app.recognition.state_snapshot import RecognitionStateSnapshot
from app.recognition.teacher_facing_summary import TeacherFacingSummary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="with_review")
    args = parser.parse_args()
    batch = run_synthetic_batch(args.scenario)
    summary_model = BatchRecognitionSummary(**batch["batch_summary"])
    teacher = TeacherFacingSummary.from_models(
        summary_model,
        batch["review_queue_summary"],
        {"total_students": batch["images"], "total_items": batch["total_items"]},
        batch["qwen_cost"],
        exam_id=batch["exam_id"],
        batch_id=batch["job_id"],
        student_statuses=batch["student_statuses"],
    )
    snapshot = RecognitionStateSnapshot(
        snapshot_id="snap-001",
        batch_id=batch["job_id"],
        status=batch["status"],
        batch_summary=batch["batch_summary"],
        review_summary=batch["review_queue_summary"],
        qwen_policy_summary=batch["qwen_policy_summary"],
        teacher_summary=teacher.to_safe_dict(),
        warnings=["synthetic_only_no_real_api"],
    )
    output = snapshot.to_safe_dict()
    output["readiness_gate"] = asdict(check_readiness())
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
