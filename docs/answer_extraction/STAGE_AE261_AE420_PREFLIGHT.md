# Stage AE261-AE420 Preflight

**Date:** 2026-07-09

## Git Status
- **Branch:** main
- **Latest commit:** `2572093 fix harden answer extraction v3`
- **Start commit:** `66daf0f fix harden answer extraction algorithm v2`
- **Working tree:** clean

## Test Results
- `python run_tests.py`: **1038 tests OK (skipped=5)**

## CLI Smoke - All 4 Types Pass
| Type | Strategy | Status | Q | A | Accepted | Grid Ignored |
|------|----------|--------|---|---|----------|---------------|
| 1 same_file_boxed | same_file_boxed | accepted | 3 | 3 | 3 | 0 |
| 2 same_file_itemized | same_file_itemized | accepted | 2 | 2 | 2 | 0 |
| 3 split_file_boxed | split_file_boxed | accepted | 3 | 3 | 3 | 0 |
| 4 split_file_itemized | split_file_itemized | accepted | 2 | 2 | 2 | 1 |

## Local Smoke
- status: `skipped` (local samples missing)

## P0 Caveats from Previous Round
1. **P0-1:** `【答案】` bracket NOT covered — only `〖答案〗` in fixtures
2. **P0-2:** Evidence guard — verify no accepted answer without evidence_text

## Current Round Goals
Fix both P0s + complete AE261-AE420 algorithm hardening

## Allowed/Forbidden Paths
- Allowed: `app/answer_extraction/**`, `tests/**`, `scripts/**`, `docs/answer_extraction/**`
- Forbidden: `legacy/**`, `app/compat/**`, `app/domain/grading/**`, `app/workflow.py`, `objective_grader.py`, `web/**`
