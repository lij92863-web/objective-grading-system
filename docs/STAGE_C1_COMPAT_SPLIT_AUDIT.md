# Stage C1 — Compatibility Split Baseline Audit

## D8 deletion count fix
- Verified: **49 files deleted** (16 old_modules + 33 old_outputs)
- D8 summary corrected from "50" to "49"

## objective_grader.py current state
- Import: `from legacy import objective_grader_legacy as legacy`
- 146 COMPAT_EXPORTS symbols
- `globals().update({name: getattr(legacy, name) for name in COMPAT_EXPORTS})`
- Main CLI path: build_parser() + main() — calls run_grading, create_sample_files
- No star import ✅
- No direct grading/report/loader calls in ordinary path ✅

## Target: split compatibility from CLI entry
- `objective_grader.py` → keep CLI entry + thin delegation
- `app/compat/objective_grader_compat.py` → new: host COMPAT_EXPORTS

## Why NOT delete legacy
- COMPAT_EXPORTS still resolves to legacy
- Tests baseline still import legacy
- Facade files still re-export legacy
