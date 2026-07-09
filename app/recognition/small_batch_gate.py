"""Small batch readiness gate v2."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class SmallBatchGateReport:
    ready_for_small_batch: bool = False
    single_anonymous_image_trial_passed: bool = False
    three_image_trial_passed: bool = False
    fixture_driven_batch_passed: bool = False
    model_driven_summary_passed: bool = False
    qwen_budget_truth_passed: bool = False
    identity_policy_passed: bool = False
    review_queue_policy_passed: bool = False
    no_real_data_leak: bool = False
    blockers: List[str] = field(default_factory=list)


def check_small_batch_gate(
    single_anonymous_image_trial_passed: bool = False,
    three_image_trial_passed: bool = False,
    fixture_driven_batch_passed: bool = False,
    model_driven_summary_passed: bool = False,
    qwen_budget_truth_passed: bool = False,
    identity_policy_passed: bool = False,
    review_queue_policy_passed: bool = False,
    no_real_data_leak: bool = False,
) -> SmallBatchGateReport:
    checks = {
        "SINGLE_ANONYMOUS_IMAGE_NOT_PASSED": single_anonymous_image_trial_passed,
        "THREE_IMAGE_TRIAL_NOT_PASSED": three_image_trial_passed,
        "FIXTURE_DRIVEN_BATCH_NOT_PASSED": fixture_driven_batch_passed,
        "MODEL_DRIVEN_SUMMARY_NOT_PASSED": model_driven_summary_passed,
        "QWEN_BUDGET_TRUTH_NOT_PASSED": qwen_budget_truth_passed,
        "IDENTITY_POLICY_NOT_PASSED": identity_policy_passed,
        "REVIEW_QUEUE_POLICY_NOT_PASSED": review_queue_policy_passed,
        "REAL_DATA_LEAK_GUARD_NOT_PASSED": no_real_data_leak,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return SmallBatchGateReport(
        ready_for_small_batch=not blockers,
        single_anonymous_image_trial_passed=single_anonymous_image_trial_passed,
        three_image_trial_passed=three_image_trial_passed,
        fixture_driven_batch_passed=fixture_driven_batch_passed,
        model_driven_summary_passed=model_driven_summary_passed,
        qwen_budget_truth_passed=qwen_budget_truth_passed,
        identity_policy_passed=identity_policy_passed,
        review_queue_policy_passed=review_queue_policy_passed,
        no_real_data_leak=no_real_data_leak,
        blockers=blockers,
    )
