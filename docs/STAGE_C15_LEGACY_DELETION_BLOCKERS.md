# Stage C15 — Legacy Deletion Blockers

## Current legacy references
- `app/compat/objective_grader_compat.py` — imports legacy for COMPAT_EXPORTS (125 symbols)
- `tests/` — 30+ test files import legacy for baseline comparison
- `legacy/objective_grader_legacy.py` — self-reference

## Blocker summary
1. **COMPAT_EXPORTS**: 125 symbols re-exported via app/compat
2. **Test baselines**: 30+ test files that import legacy for comparison
3. **No app/ main-chain imports**: ✅ (only app/compat)

## To delete legacy main file, must first:
1. Replace all test baseline imports with fixture-based equivalents
2. Narrow COMPAT_EXPORTS to only truly externally-used symbols
3. Confirm no external scripts depend on legacy

## Conclusion: DO NOT delete legacy/objective_grader_legacy.py this round
