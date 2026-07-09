# Stage R201-R280 Preflight

Branch: main

Starting commit: 201fee5 feat add fixture-driven batch, safety regression matrix, docs

Initial status: clean before edits.

Allowed paths used: app/recognition, app/recognition/qwen_adapter, scripts, tests, tests/fixtures/recognition, docs/recognition.

Forbidden paths not edited: legacy, app/compat, grading core, app/workflow.py, objective_grader.py, web, dependency files.

Real Qwen API: not executed. The default Qwen sample path remains fail-closed unless `--allow-real-api` is explicitly passed.

Preflight commands and results:

| Command | Result |
| --- | --- |
| `git status --short` | clean before edits |
| `git branch --show-current` | main |
| `git log --oneline -12` | 201fee5 at HEAD before edits |
| `python run_tests.py` | passed, 697 tests before edits |
| `python -m unittest discover` | initially found no tests; fixed with `tests/__init__.py` |
| `python scripts/run_controlled_recognition_fixture.py --dry-run` | initially missing defaults; fixed and passed |
| `python scripts/run_controlled_qwen_sample.py` | fail-closed, no real API |
| `python scripts/run_controlled_qwen_sample.py --check-only` | initially unsupported; fixed and passed |
| `python scripts/validate_recognition_template.py --template tests/fixtures/recognition/layouts/demo_layout.json` | passed |
| `python scripts/audit_recognition_templates.py` | reports 5 valid and 1 known invalid template; command now exits 0 |
| `python scripts/evaluate_recognition_golden_suite.py` | passed |
| `python scripts/run_synthetic_recognition_dry_run.py` | passed |
| `python scripts/run_synthetic_batch_recognition.py --scenario all_clear --count 3 --json` | passed after fixture-driven rewrite |
| `python scripts/run_synthetic_batch_recognition.py --scenario with_review --count 3 --json` | passed after fixture-driven rewrite |
| `python scripts/run_synthetic_batch_recognition.py --scenario with_blocking_identity --count 3 --json` | passed after fixture-driven rewrite |
| `python scripts/run_synthetic_batch_recognition.py --scenario qwen_budget_exceeded --count 3 --json` | passed after fixture-driven rewrite |
| `python scripts/evaluate_synthetic_batch.py --all` | passed, 8 of 8 fixtures |
| `python scripts/run_teacher_summary_synthetic.py --scenario with_review` | passed |
| `python scripts/run_teacher_summary_synthetic.py --scenario with_blocking_identity` | passed |
| `python scripts/check_real_paper_readiness.py` | default false |
| `python scripts/check_small_batch_gate.py` | missing initially; added, default false |

Remaining caveats:

- No real paper trial has been run.
- No real class or small batch use is allowed.
- No formal CSV, Excel, or HTML grading report is generated from recognition.
- The next real-paper step must start with one anonymous image, manual ROI, and Qwen check-only.
