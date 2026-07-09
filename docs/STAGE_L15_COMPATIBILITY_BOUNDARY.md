# Stage L15 — CLI Compatibility Boundary

## Status: Retained for compatibility

`objective_grader.py` uses explicit `COMPAT_EXPORTS` tuple (146 symbols) re-exported from legacy for backward compatibility with external scripts and tests.

## Classification
- **Already migrated internally**: grade_all, loaders, report writers → not called via legacy in main path
- **Compatibility-only**: COMPAT_EXPORTS serves old scripts that `import objective_grader`
- **Deletion candidates (future)**: symbols already available via `app.domain.grading`, `app.infrastructure.*`
- **Non-deletable (current)**: symbols with no equivalent in new app structure yet

## Decision: Retain, do not shrink now
- External scripts may depend on these exports
- Premature removal risks breakage
- Defer to controlled deletion cleanup
