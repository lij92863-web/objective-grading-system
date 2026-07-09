# Stage AE001-AE120 Preflight

Branch: main

Start commit: 07dd3d7 feat harden controlled single qwen trial gate

Initial status: clean

Commands run before implementation:

- `git status --short`: clean
- `python run_tests.py`: passed, 984 tests OK, 5 skipped
- `python -m unittest discover`: passed, 971 tests OK, 5 skipped
- `python scripts/run_controlled_qwen_sample.py`: fail-closed as expected, real API disabled
- `python scripts/run_controlled_qwen_sample.py --check-only`: passed, no real API call
- `python scripts/check_real_paper_readiness.py --json`: passed, default false with blockers
- `python scripts/check_small_batch_gate.py --json`: completed, ready false with blockers

Goal: build a deterministic teacher document answer extraction engine for question indexes, answer keys, alignment reports, extraction reports, and review items.

Allowed paths used: `app/answer_extraction/**`, `app/application/use_cases/answer_extraction/**`, `app/infrastructure/answer_extraction/**`, `tests/**`, `tests/fixtures/answer_extraction/**`, `scripts/**`, `docs/answer_extraction/**`, `docs/product/**`.

Forbidden boundaries: no real Qwen API, no `.env` reads, no grading integration, no workflow integration, no web integration, no dependency file changes, no formal score CSV/Excel/HTML reports.
