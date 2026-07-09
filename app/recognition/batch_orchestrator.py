"""R93A: Batch orchestrator — synthetic."""
from dataclasses import dataclass, field
from typing import List, Dict
from .contracts import RecognitionDecision
from .batch_job import RecognitionBatchJob
from .batch_summary import count_from_decisions
from .review_queue_builder import build_review_queue, summary as queue_summary


SCENARIOS = {
    "all_clear": {"review_fraction": 0.0, "blocking_fraction": 0.0},
    "with_review": {"review_fraction": 0.15, "blocking_fraction": 0.0},
    "with_blocking_identity": {"review_fraction": 0.1, "blocking_fraction": 0.08},
    "qwen_budget_exceeded": {"review_fraction": 0.4, "blocking_fraction": 0.0},
}


def run_synthetic_batch(scenario: str = "all_clear", count: int = 3) -> dict:
    cfg = SCENARIOS.get(scenario, SCENARIOS["all_clear"])
    job = RecognitionBatchJob(job_id=f"batch-{scenario}", exam_id="exam-001",
                               template_id="demo_v1", image_asset_ids=[f"asset-{i}" for i in range(count)])
    job.transition("running")
    decs_per = []
    for i in range(count):
        n = 5
        decs = []
        for q in range(1, n + 1):
            if i == 0 and cfg["blocking_fraction"] > 0 and q <= max(1, int(n * cfg["blocking_fraction"])):
                decs.append(RecognitionDecision(question_number=q, value="", status="invalid",
                                                 blocking=True, needs_review=True, reason="identity_conflict"))
            elif cfg["review_fraction"] > 0 and q <= max(1, int(n * cfg["review_fraction"])):
                decs.append(RecognitionDecision(question_number=q, value="?", status="needs_review",
                                                 needs_review=True, reason="omr_qwen_conflict"))
            else:
                decs.append(RecognitionDecision(question_number=q, value="A", status="auto_accepted",
                                                 needs_review=False))
        decs_per.append(decs)
    s = count_from_decisions(decs_per)
    items = []
    for decs in decs_per:
        items.extend(build_review_queue(decs, student_ref="S001", draft_id="d1"))
    qs = queue_summary(items)
    has_review = any(d.needs_review for decs in decs_per for d in decs)
    has_blocking = any(d.blocking for decs in decs_per for d in decs)
    if has_blocking: job.transition("blocked")
    elif has_review: job.transition("completed_with_review")
    else: job.transition("completed")
    return {"job_id": job.job_id, "status": job.status, "images": count,
            "batch_summary": s.__dict__,
            "review_queue_summary": qs,
            "qwen_cost": {"calls": s.qwen_call_count, "estimated_cost": s.estimated_cost,
                          "status": "exceeds_limit" if s.qwen_call_count > 10 else "within_limit"}}
