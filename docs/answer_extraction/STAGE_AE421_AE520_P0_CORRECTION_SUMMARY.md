# Stage AE421-AE520 P0 Correction and Anti-Shitshan Lockdown Summary

**Date:** 2026-07-09

## Git
- **Branch:** main
- **Start commit:** `a5172cf`
- **End commit:** (after push)

## What Was Fixed

The core `【答案】` support was already correctly implemented in the regex and fixtures.
This round added structural anti-shitshan guards to prevent future regression.

### 【答案】Code Support Evidence
- `answer_markers.py` created: `REAL_CHINESE_ANSWER_MARKER = "【答案"` is the primary marker
- `itemized_answer_extractor.py` now imports `ANSWER_MARKER_RE` instead of hand-rolling regex
- `status_model.py` created: `FINAL_ACCEPTED_STATUSES`, `is_final_accepted_status()`
- `answer_key_validator.py` uses status constants
- `evidence_invariant.py` uses status constants

### 【答案】Fixture Evidence
- All v3 `real_chinese_brackets` fixtures contain `【答案】` (verified by audit)
- All v3 `real_chinese_brackets` fixtures contain 0 `〖答案〗` (verified by audit)

### 【答案】Test Assertion Evidence
- `test_itemized_answer_extractor_chinese_bracket_p0.py` line 23: `assertIn("【答案】", candidate.evidence_text)`
- `test_cli_real_chinese_brackets_evidence_p0.py`: verifies CLI outputs `【答案】`
- `test_synthetic_docx_real_brackets_p0.py`: verifies DOCX contains `【答案】`

### CLI Evidence
```
python extract_answer_key.py --file ...type2_same_file_itemized_with_real_chinese_brackets.json --json --show-evidence
→ Q1: has_real_bracket=True, Q2: has_real_bracket=True
```

## Compat Bracket Retention
- `〖答案〗` and `[答案]` still supported via `COMPAT_ANSWER_MARKERS`
- `test_itemized_answer_extractor_compat_brackets.py` verifies compat still works

## Anti-Shitshan Guards Added
- `test_answer_extraction_fixture_truthfulness_guard.py` — prevents fake real brackets
- `test_answer_extraction_no_cosmetic_pass_guard.py` — prevents cosmetic passes
- `test_answer_extraction_status_model_guard.py` — ensures status constants used
- `test_answer_source_policy_usage_guard.py` — ensures confidence from policy
- `test_answer_markers.py` — validates marker definitions

## Files Created
### Source
- `app/answer_extraction/answer_markers.py`
- `app/answer_extraction/status_model.py`

### Tests (10 new)
1. `test_answer_markers.py`
2. `test_answer_extraction_fixture_truthfulness_guard.py`
3. `test_answer_extraction_no_cosmetic_pass_guard.py`
4. `test_answer_extraction_status_model_guard.py`
5. `test_cli_real_chinese_brackets_evidence_p0.py`
6. `test_synthetic_docx_real_brackets_p0.py`
7. `test_itemized_answer_extractor_compat_brackets.py`
8. `test_evidence_invariant_engine_output_p0.py`
9. `test_answer_source_policy_usage_guard.py`

### Docs (5 new/updated)
1. `STAGE_AE421_AE520_PREFLIGHT.md`
2. `STAGE_AE421_P0_BRACKET_AUDIT.md`
3. `FIXTURE_NAMING_AUDIT_AE421.md`
4. `ANTI_SHITSHAN_RULES.md`
5. `STAGE_AE421_AE520_P0_CORRECTION_SUMMARY.md`

## Test Results
- `python run_tests.py`: **1243 tests OK (skipped=5)**
- All anti-shitshan guard tests pass

## Available Pipeline
- JSON/DOCX → extract_answer_key → validated answer key with `【答案】` support
- Fixture truthfulness enforcement
- CLI evidence verification

## Unavailable
- Real Qwen API
- Student answer card recognition
- Grading/workflow/web integration
