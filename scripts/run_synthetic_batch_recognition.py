#!/usr/bin/env python3
"""R93: Synthetic batch recognition CLI."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.contracts import RecognitionDecision
from app.recognition.batch_job import RecognitionBatchJob
from app.recognition.batch_summary import count_from_decisions


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=3)
    args = p.parse_args()
    job = RecognitionBatchJob(job_id="batch-001", exam_id="exam-001",
                               template_id="demo_v1", image_asset_ids=[f"asset-{i}" for i in range(args.count)])
    job.transition("running")
    decs_per = [[RecognitionDecision(question_number=i, value="A", status="auto_accepted", needs_review=False) for i in range(1,6)]
                 for _ in range(args.count)]
    s = count_from_decisions(decs_per)
    job.summary = {"batch": s.__dict__}
    job.transition("completed")
    result = {"job_id": job.job_id, "status": job.status, "images": job.image_asset_ids, "summary": job.summary}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
