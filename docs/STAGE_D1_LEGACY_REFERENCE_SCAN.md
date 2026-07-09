# Stage D1 — Legacy Reference Scan

> Date: 2026-07-09

## workflow.py legacy references
- `from legacy import objective_grader_legacy as legacy`
- Uses: `legacy.ExamMeta`, `legacy.load_question_bank`, legacy type hints
- **Targets to remove this round**: ExamMeta, load_question_bank → then remove entire import

## objective_grader.py legacy references
- `from legacy import objective_grader_legacy as legacy` (for COMPAT_EXPORTS only)
- 146 symbols re-exported via `globals().update()`

## app/domain/application/infrastructure/shared
- **No legacy imports** ✅ (already verified by guard matrix)

## ExamMeta usage
- `app/workflow.py` — constructs `legacy.ExamMeta(...)` (L466)
- `app/core.py` — facade re-export
- `objective_grader.py` — COMPAT_EXPORTS
- Tests: 6 files for baseline

## load_question_bank usage
- `app/workflow.py` — calls `legacy.load_question_bank(path)` (L473)
- `app/core.py` — facade re-export
- `objective_grader.py` — COMPAT_EXPORTS
- `web_app.py` — web usage (out of scope, don't touch)
- Tests: 3 files

## old_modules / deletion candidates
- `legacy/old_modules/` — analyst, core, io, workflow subdirs
- `legacy/old_outputs/reports/` — old report files
- These are NOT imported by any app/ file
- Tests do NOT import from these
- **Candidate A**: zero-reference, can delete

## This round targets
1. ExamMeta → `app/application/contracts/exam_metadata.py`
2. load_question_bank → `app/infrastructure/loaders/question_bank_loader.py`
3. workflow → zero legacy import
4. Delete `legacy/old_modules/` and `legacy/old_outputs/` (zero-reference)
