# Stage AE421-AE520 Preflight

**Date:** 2026-07-09

## Git Status
- **Branch:** main
- **Start commit:** `a5172cf`
- **Working tree:** clean

## Test Results
- `python run_tests.py`: **1195 tests OK (skipped=5)**

## P0 Bracket Audit (empirical)
- v3 `real_chinese_brackets` fixtures: ALL contain `【答案】`, 0 contain `〖答案〗`
- `itemized_answer_extractor.py` regex: supports `【答案】` + `〖答案〗` + `[答案]`
- Test at line 23: `assertIn("【答案】", candidate.evidence_text)`
- Synthetic DOCX: `same_file_itemized_real_brackets.docx` contains `【答案】`

## Current P0 Bracket Problem
The core implementation is already correct, but structural safeguards are missing:
1. No centralized `answer_markers.py` (regex hand-rolled in extractor)
2. No `status_model.py` (status strings scattered)
3. No fixture truthfulness guard
4. No compat bracket separation in fixtures

## Round Goals
AE421-AE520: Add structural anti-shitshan guards without breaking existing functionality.

## Allowed/Forbidden Paths
Same as previous round.
