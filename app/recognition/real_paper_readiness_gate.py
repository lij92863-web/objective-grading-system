"""R140: Real paper readiness gate."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ReadinessReport:
    ready_for_single_real_qwen_trial: bool = False
    ready_for_three_image_trial: bool = False
    ready_for_small_batch_trial: bool = False
    has_fixture_driven_batch: bool = False
    has_model_driven_teacher_summary: bool = False
    has_qwen_budget_truth_tests: bool = False
    has_exact_identity_error_registry: bool = False
    has_review_action_policy: bool = False
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def check_readiness(has_anonymous_image: bool = False, has_template: bool = True,
                     has_manual_roi: bool = False, qwen_check_only_passed: bool = False,
                     qwen_api_key_present: bool = False, no_real_data_committed: bool = True,
                     review_queue_ready: bool = False, batch_policy_ready: bool = False,
                     has_fixture_driven_batch: bool = False,
                     has_model_driven_teacher_summary: bool = False,
                     has_qwen_budget_truth_tests: bool = False,
                     has_exact_identity_error_registry: bool = False,
                     has_review_action_policy: bool = False) -> ReadinessReport:
    blockers = []
    if not has_anonymous_image: blockers.append("NO_ANONYMOUS_IMAGE")
    if not has_template: blockers.append("NO_TEMPLATE")
    if not has_manual_roi: blockers.append("NO_MANUAL_ROI")
    if not qwen_check_only_passed: blockers.append("QWEN_CHECK_ONLY_NOT_PASSED")
    if not qwen_api_key_present: blockers.append("NO_QWEN_API_KEY")
    if not has_fixture_driven_batch: blockers.append("NO_FIXTURE_DRIVEN_BATCH_SIGNOFF")
    if not has_model_driven_teacher_summary: blockers.append("NO_MODEL_DRIVEN_TEACHER_SUMMARY_SIGNOFF")
    if not has_qwen_budget_truth_tests: blockers.append("NO_QWEN_BUDGET_TRUTH_SIGNOFF")
    if not has_exact_identity_error_registry: blockers.append("NO_EXACT_IDENTITY_REGISTRY_SIGNOFF")
    if not has_review_action_policy: blockers.append("NO_REVIEW_ACTION_POLICY_SIGNOFF")
    single_ready = len(blockers) == 0
    three_ready = single_ready and qwen_check_only_passed
    small_batch_ready = three_ready and review_queue_ready and batch_policy_ready
    return ReadinessReport(ready_for_single_real_qwen_trial=single_ready,
                            ready_for_three_image_trial=three_ready,
                            ready_for_small_batch_trial=small_batch_ready,
                            has_fixture_driven_batch=has_fixture_driven_batch,
                            has_model_driven_teacher_summary=has_model_driven_teacher_summary,
                            has_qwen_budget_truth_tests=has_qwen_budget_truth_tests,
                            has_exact_identity_error_registry=has_exact_identity_error_registry,
                            has_review_action_policy=has_review_action_policy,
                            blockers=blockers)
