# Stage C7 — Compat Module Deletion Readiness

## Why app/compat was created
- Isolate the ONLY legacy import to a single controlled location
- objective_grader.py no longer imports legacy directly
- Clear separation: CLI entry vs compatibility facade

## Current state
- `objective_grader.py`: does NOT import legacy ✅
- `app/compat/objective_grader_compat.py`: imports legacy (ONLY allowed app/ location) ✅
- COMPAT_EXPORTS: 146 symbols
- `app/workflow.py`: no legacy import ✅
- `app/domain`, `app/application`, `app/infrastructure`, `app/shared`: no legacy import ✅

## Why 146 symbols are retained
- Old scripts may import from `objective_grader`
- Tests baseline import from legacy for comparison
- Facade files (analysis.py, reports.py, core.py) re-export
- Premature shrinking risks external breakage

## When legacy main file can be deleted
1. All compatibility tests pass through app/compat (not direct legacy)
2. Facade files (analysis.py, reports.py, core.py) updated or removed
3. All baseline tests replaced with new-module equivalents
4. External scripts confirmed migrated

## Next step recommendation
**C9: COMPAT_EXPORTS classification shrink** — classify each of 146 symbols as:
- Already migrated internally (can remove from exports)
- Still needed for compatibility (keep)
- Internal-only (can remove)
