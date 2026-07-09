# Stage R201 Fixture Usage Audit

Audited starting point: 201fee5.

Findings before this change:

| Area | Finding |
| --- | --- |
| Synthetic batch fixtures | JSON files existed, but they were thin summaries with `expected_*` fields only. |
| `run_synthetic_batch_recognition.py` | Selected hard-coded scenarios and did not support `--fixture`. |
| `evaluate_synthetic_batch.py` | Returned a hard-coded result and did not compare fixture expected values. |
| `batch_orchestrator.py` | Used `SCENARIOS` with `review_fraction` and `blocking_fraction`. |
| `qwen_budget_exceeded` | Simulated review volume; budget guard counters were not the source of truth. |
| Teacher summary | Script assembled counts directly and included blocked/ready shortcuts. |
| Identity checks | Some code paths still used substring checks on identity reason text. |

Replaced paths:

- `batch_orchestrator.py` now loads v4 fixtures through `SyntheticBatchLoader`.
- `evaluate_synthetic_batch.py` now compares actual orchestrator output with fixture `expected`.
- `run_synthetic_batch_recognition.py` now supports `--fixture` and fail-closed unknown scenarios.
- `qwen_budget_exceeded` now uses `QwenPolicyOrchestrator` and budget counters.
- Teacher summary CLI now uses `TeacherFacingSummary.from_models`.
- Identity safety checks now use `IDENTITY_ERROR_CODES` exact membership.

Fixtures connected in this round:

- `batch_all_clear.json`
- `batch_with_review.json`
- `batch_with_blocking_identity.json`
- `batch_qwen_budget_exceeded.json`
- `batch_mixed_choice_blank_identity.json`
- `batch_malformed_qwen_response.json`
- `batch_missing_roi.json`
- `batch_invalid_option.json`

No real Qwen API, grade_all, or report generation path is used by these synthetic fixtures.
