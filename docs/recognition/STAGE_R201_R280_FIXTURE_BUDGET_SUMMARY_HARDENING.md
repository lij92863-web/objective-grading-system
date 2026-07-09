# Stage R201-R280 Fixture, Budget, Summary Hardening

Starting commit: 201fee5 feat add fixture-driven batch, safety regression matrix, docs

End commit: f62858a fix make synthetic batch fixture-driven and qwen budget truthful

Push: pending at document update time; final reply records the pushed state.

Completed:

- synthetic batch is fixture-driven through `SyntheticBatchLoader`
- `evaluate_synthetic_batch.py` validates expected vs actual
- `qwen_budget_exceeded` is produced by `QwenPolicyOrchestrator`
- `blocked_by_budget_count` is a real counter
- teacher summary uses `TeacherFacingSummary.from_models`
- identity checks use exact error code registry sets
- readiness gate defaults false
- small batch gate defaults false
- state snapshot is debug-safe and synthetic-only

Test commands run:

- `python run_tests.py`
- `python -m unittest discover`
- `python scripts/run_controlled_recognition_fixture.py --dry-run`
- `python scripts/run_controlled_qwen_sample.py`
- `python scripts/run_controlled_qwen_sample.py --check-only`
- `python scripts/validate_recognition_template.py --template tests/fixtures/recognition/layouts/demo_layout.json`
- `python scripts/audit_recognition_templates.py`
- `python scripts/evaluate_recognition_golden_suite.py`
- `python scripts/run_synthetic_recognition_dry_run.py`
- `python scripts/run_synthetic_batch_recognition.py --scenario all_clear --count 3 --json`
- `python scripts/run_synthetic_batch_recognition.py --scenario with_review --count 3 --json`
- `python scripts/run_synthetic_batch_recognition.py --scenario with_blocking_identity --count 3 --json`
- `python scripts/run_synthetic_batch_recognition.py --scenario qwen_budget_exceeded --count 3 --json`
- `python scripts/run_synthetic_batch_recognition.py --fixture tests/fixtures/recognition/synthetic_batches/batch_qwen_budget_exceeded.json --json`
- `python scripts/evaluate_synthetic_batch.py --all`
- `python scripts/run_teacher_summary_synthetic.py --scenario with_review`
- `python scripts/run_teacher_summary_synthetic.py --scenario with_blocking_identity`
- `python scripts/run_teacher_summary_synthetic.py --scenario qwen_budget_exceeded`
- `python scripts/check_real_paper_readiness.py --json`
- `python scripts/check_small_batch_gate.py --json`
- `python scripts/run_recognition_state_snapshot_synthetic.py --scenario with_review`

Safety boundaries:

- no real Qwen API executed
- no `.env` read
- no raw API response saved
- no base64 image output
- no real student image committed
- no `data/tmp` or `data/reports` committed
- no legacy, app/compat, grading core, workflow, objective_grader, web, or dependency file edits

Current usable chain:

fixture -> loader -> orchestrator -> review queue -> batch summary -> teacher summary -> synthetic snapshot

Current unavailable chain:

real paper -> real Qwen -> formal grading -> formal class reports

Real paper next step:

anonymous single image -> manual ROI -> Qwen check-only -> explicit real API trial -> sanitized audit -> parser audit -> review queue audit.
