"""Fixture-driven synthetic batch orchestrator."""
from copy import deepcopy
from dataclasses import asdict
from typing import Dict, List

from .batch_job import RecognitionBatchJob
from .batch_summary import BatchRecognitionSummary
from .contracts import RecognitionDecision
from .error_codes import BLOCKING_ERROR_CODES
from .qwen_adapter.policy_orchestrator import QwenPolicyOrchestrator
from .review_queue_builder import build_review_queue, summary as queue_summary
from .synthetic_batch_loader import load_fixture_by_path, load_fixture_by_scenario


def _question_number(question_id) -> int:
    digits = "".join(ch for ch in str(question_id) if ch.isdigit())
    return int(digits or 0)


def _expand_fixture(fixture, count: int | None):
    if count is None or count == len(fixture.students):
        return fixture.students, fixture.items
    if count <= 0:
        raise ValueError("count must be positive")
    students = []
    items = []
    source_students = fixture.students
    for idx in range(count):
        original = source_students[idx % len(source_students)]
        student = deepcopy(original)
        student["student_ref"] = f"S{idx + 1:03d}"
        if idx >= len(source_students):
            student["display_name"] = f"{original.get('display_name', 'Student')} {idx + 1}"
        students.append(student)
        original_ref = original["student_ref"]
        for item in fixture.items:
            if item["student_ref"] != original_ref:
                continue
            cloned = deepcopy(item)
            cloned["student_ref"] = student["student_ref"]
            items.append(cloned)
    return students, items


def _decision_from_fixture_item(item: dict, qwen_policy: QwenPolicyOrchestrator) -> RecognitionDecision:
    exception_codes = list(item.get("expected_exception_codes") or [])
    status = item.get("expected_decision_status", "auto_accepted")
    qwen_required = bool(item.get("qwen_required"))

    if qwen_required:
        decision = qwen_policy.decide(
            omr_confidence=item.get("omr_confidence"),
            is_blank=item.get("question_type") == "blank",
            omr_clear=False,
            image_sha256=f"fixture-{item.get('student_ref')}",
            roi_id=str(item.get("question_id")),
        )
        if decision.blocked_by_budget:
            exception_codes = ["qwen_budget_exceeded"]
            status = "needs_review"
        elif item.get("qwen_response_kind") == "malformed":
            exception_codes = ["malformed_response"]
            status = "needs_review"
    if exception_codes and status == "auto_accepted":
        status = "needs_review"
    blocking = any(code in BLOCKING_ERROR_CODES for code in exception_codes)
    needs_review = status == "needs_review" or blocking or bool(exception_codes)
    reason = exception_codes[0] if exception_codes else ""
    return RecognitionDecision(
        question_number=_question_number(item.get("question_id")),
        value=item.get("omr_answer", ""),
        normalized_value=item.get("omr_answer", ""),
        status="needs_review" if needs_review else "auto_accepted",
        confidence=float(item.get("omr_confidence") or 0.0),
        source_engines=[item.get("source", "fixture")],
        needs_review=needs_review,
        blocking=blocking,
        reason=reason,
    )


def _student_status(student_ref: str, decisions: List[RecognitionDecision]) -> str:
    if any(decision.blocking for decision in decisions):
        return "blocked"
    if any(decision.needs_review for decision in decisions):
        return "needs_review"
    return "ready"


def run_synthetic_batch(scenario: str = "all_clear", count: int | None = None,
                        fixture_path: str | None = None) -> dict:
    fixture = load_fixture_by_path(fixture_path) if fixture_path else load_fixture_by_scenario(scenario)
    students, items = _expand_fixture(fixture, count)
    qwen_budget = fixture.qwen_budget
    qwen_policy = QwenPolicyOrchestrator(
        max_qwen_calls=int(qwen_budget.get("max_calls", 0)),
        qwen_enabled=bool(qwen_budget.get("enabled", False)),
    )
    job = RecognitionBatchJob(
        job_id=fixture.batch_id,
        exam_id=fixture.exam_id,
        template_id="synthetic_fixture_v4",
        image_asset_ids=[student["student_ref"] for student in students],
    )
    job.transition("running")

    decisions_by_student: Dict[str, List[RecognitionDecision]] = {student["student_ref"]: [] for student in students}
    review_items = []
    for item in items:
        decision = _decision_from_fixture_item(item, qwen_policy)
        student_ref = item["student_ref"]
        decisions_by_student.setdefault(student_ref, []).append(decision)
        exceptions = [{"code": decision.reason, "question_number": decision.question_number}] if decision.reason else []
        review_items.extend(build_review_queue([decision], student_ref=student_ref,
                                                draft_id=f"draft-{student_ref}", exceptions=exceptions))

    batch_summary = BatchRecognitionSummary(
        job_id=job.job_id,
        total_images=len(students),
        processed_images=len(students),
        auto_accepted_items=sum(
            1 for decisions in decisions_by_student.values()
            for decision in decisions if decision.status == "auto_accepted" and not decision.needs_review
        ),
        needs_review_items=sum(
            1 for decisions in decisions_by_student.values()
            for decision in decisions if decision.needs_review
        ),
        blocking_items=sum(
            1 for decisions in decisions_by_student.values()
            for decision in decisions if decision.blocking
        ),
    )
    policy_summary = qwen_policy.summary()
    batch_summary.qwen_call_count = policy_summary["qwen_call_allowed_count"]
    batch_summary.qwen_needed_count = policy_summary["qwen_needed_count"]
    batch_summary.qwen_call_skipped_count = policy_summary["qwen_call_skipped_count"]
    batch_summary.blocked_by_budget_count = policy_summary["blocked_by_budget_count"]
    batch_summary.cache_hit_count = policy_summary["cache_hit_count"]
    batch_summary.omr_only_count = batch_summary.qwen_call_skipped_count
    batch_summary.estimated_cost = batch_summary.qwen_call_count * 0.002

    student_statuses = {
        student["student_ref"]: _student_status(student["student_ref"], decisions_by_student.get(student["student_ref"], []))
        for student in students
    }
    if any(status == "blocked" for status in student_statuses.values()):
        job.transition("blocked")
    elif any(status == "needs_review" for status in student_statuses.values()):
        job.transition("completed_with_review")
    else:
        job.transition("completed")

    qs = queue_summary(review_items)
    qwen_cost = {
        "calls": batch_summary.qwen_call_count,
        "estimated_cost": batch_summary.estimated_cost,
        "status": "exceeds_limit" if batch_summary.blocked_by_budget_count else "within_limit",
        "qwen_needed_count": batch_summary.qwen_needed_count,
        "qwen_call_skipped_count": batch_summary.qwen_call_skipped_count,
        "blocked_by_budget_count": batch_summary.blocked_by_budget_count,
        "cache_hit_count": batch_summary.cache_hit_count,
    }
    return {
        "job_id": job.job_id,
        "exam_id": fixture.exam_id,
        "scenario": fixture.scenario,
        "status": job.status,
        "images": len(students),
        "batch_summary": asdict(batch_summary),
        "review_queue_summary": qs,
        "qwen_cost": qwen_cost,
        "qwen_policy_summary": policy_summary,
        "student_statuses": student_statuses,
        "total_items": sum(len(decisions) for decisions in decisions_by_student.values()),
    }
