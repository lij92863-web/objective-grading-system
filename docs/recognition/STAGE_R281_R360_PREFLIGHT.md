# Stage R281-R360 Preflight

Branch: main

Starting commit: a00e393 fix make synthetic batch fixture-driven and qwen budget truthful

Initial git status: clean.

This round has no real paper, no real image, and no real Qwen API execution.

Allowed paths: app/recognition, app/recognition/qwen_adapter, app/application/use_cases/recognition, app/infrastructure/recognition, tests, tests/fixtures/recognition, scripts, docs/recognition, docs/deployment, docs/product.

Forbidden paths: legacy, app/compat, objective_grader.py, app/workflow.py, app/domain/grading, report builders, exporters, web, README.md, dependency files, .env.

Previous completed capability: fixture-driven synthetic batch, budget truth counters, model-driven teacher summary, readiness and small-batch gates default false.

This round target: prepare contracts and dry-run tooling for a future single anonymous image trial.

Preflight results:

| Command | Result |
| --- | --- |
| `git status --short` | clean |
| `git branch --show-current` | main |
| `git log --oneline -12` | HEAD was a00e393 |
| `python run_tests.py` | passed, 732 tests |
| `python -m unittest discover` | passed |
| `python scripts/run_controlled_recognition_fixture.py --dry-run` | passed |
| `python scripts/run_controlled_qwen_sample.py` | fail-closed by design, no real API |
| `python scripts/run_controlled_qwen_sample.py --check-only` | passed, no real API |
| `python scripts/validate_recognition_template.py --template tests/fixtures/recognition/layouts/demo_layout.json` | passed |
| `python scripts/audit_recognition_templates.py` | passed, reports one known invalid template |
| `python scripts/evaluate_recognition_golden_suite.py` | passed |
| `python scripts/run_synthetic_recognition_dry_run.py` | passed |
| `python scripts/run_synthetic_batch_recognition.py --scenario all_clear --count 3 --json` | passed |
| `python scripts/run_synthetic_batch_recognition.py --scenario with_review --count 3 --json` | passed |
| `python scripts/run_synthetic_batch_recognition.py --scenario with_blocking_identity --count 3 --json` | passed |
| `python scripts/run_synthetic_batch_recognition.py --scenario qwen_budget_exceeded --count 3 --json` | passed |
| `python scripts/run_synthetic_batch_recognition.py --fixture tests/fixtures/recognition/synthetic_batches/batch_qwen_budget_exceeded.json --json` | passed |
| `python scripts/evaluate_synthetic_batch.py --all` | passed, 8 of 8 fixtures |
| `python scripts/run_teacher_summary_synthetic.py --scenario with_review` | passed |
| `python scripts/run_teacher_summary_synthetic.py --scenario with_blocking_identity` | passed |
| `python scripts/run_teacher_summary_synthetic.py --scenario qwen_budget_exceeded` | passed |
| `python scripts/check_real_paper_readiness.py --json` | default false |
| `python scripts/check_small_batch_gate.py --json` | default false |
| `python scripts/run_recognition_state_snapshot_synthetic.py --scenario with_review` | passed |
