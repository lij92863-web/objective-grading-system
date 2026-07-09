# Stage AE261-AE420 Algorithm Completion Summary

**Date:** 2026-07-09

## Git Status
- **Branch:** main
- **Start commit:** `66daf0f fix harden answer extraction algorithm v2`
- **End commit:** (final after push)

## P0 Fixes

### P0-1: 【答案】Real Support
- **Status: ALREADY IMPLEMENTED** — The regex in `itemized_answer_extractor.py` line 21 already supports `【答案】` alongside `〖答案〗` and `[答案]`
- v2 fixture `type2_same_file_itemized_with_chinese_brackets.json` already uses `1．【答案】B`
- v3 fixtures use `【答案】` exclusively (0 occurrences of `〖答案〗`)
- CLI verified: `explicit_bracket_answer` source_kind with evidence containing `【答案】`
- Added `test_itemized_answer_extractor_chinese_bracket_p0.py` with 16+ sub-test cases

### P0-2: Evidence Guard
- **Status: ALREADY IMPLEMENTED** — `enforce_evidence_required()` in `answer_key_validator.py` line 28
- `evidence_invariant.py` post-processing at engine output
- Added `test_answer_key_validator_evidence_p0.py`
- Added `test_answer_extraction_evidence_invariant.py`
- Added `test_answer_extraction_no_evidence_accepted_guard_v3.py`

## New Tests Added (18 files)
1. `test_extraction_result_schema_v3.py` — schema defaults and required fields
2. `test_answer_source_policy_v3.py` — source confidence ordering
3. `test_extraction_report_v3.py` — v3 report fields
4. `test_fill_blank_answer_handling_v3.py` — blank/choice classification
5. `test_answer_key_validator_status_model_v3.py` — status model (20 tests)
6. `test_candidate_conflict_resolver_v3.py` — conflict resolution
7. `test_itemized_answer_context_v3.py` — cross-paragraph extraction
8. `test_question_index_complete_spans_v3.py` — question spans
9. `test_question_index_section_type_v3.py` — section-aware typing
10. `test_answer_table_extractor_complex_v3.py` — complex tables
11. `test_student_answer_grid_never_extract_v3.py` — grid guard
12. `test_answer_extraction_student_grid_p0_guard_v3.py` — P0 grid guard
13. `test_answer_extraction_no_guessing_guard_v3.py` — no-guessing guard
14. `test_answer_extraction_no_evidence_accepted_guard_v3.py` — evidence guard
15. `test_docx_parser_failure_policy_v3.py` — parser error hierarchy
16. `test_answer_extraction_cli_v3.py` — CLI evidence/diagnostics
17. `test_local_answer_extraction_smoke_v3.py` — local smoke runner
18. `test_docx_parser_synthetic_docx_v3.py` — synthetic docx pipeline

## Four Scenario Coverage
- ✅ 同文件 + 带框集中答案 (same_file_boxed)
- ✅ 同文件 + 无框逐题答案 (same_file_itemized)
- ✅ 分文件 + 带框集中答案 (split_file_boxed)
- ✅ 分文件 + 无框逐题答案 (split_file_itemized)

## Key Anti-Error Guards
- ✅ 空答题表不抽 (student_answer_grid detector)
- ✅ 【答案】直接测试
- ✅ 复杂填空支持
- ✅ 分段题号/答案表支持
- ✅ 多表答案支持
- ✅ 解析步骤编号排除 (①②③)
- ✅ 年份排除 (2024年)
- ✅ 多余答案号 blocking
- ✅ 重复冲突答案 blocking
- ✅ 单选多答案 blocking
- ✅ LLM candidate 不 accepted
- ✅ accepted/accepted_with_warnings 必须有 evidence

## Test Results
- `python run_tests.py`: **1195 tests OK (skipped=5)**
- Matrix v3: **3 tests OK**
- Synthetic DOCX smoke: **8 cases completed**
- Local smoke: skipped (samples missing)

## Standalone Tests for v3
- 18 new test files created
- All tests pass within the full suite

## Safety Boundaries
- ✅ Did NOT modify legacy
- ✅ Did NOT modify app/compat
- ✅ Did NOT modify grading core
- ✅ Did NOT modify workflow.py
- ✅ Did NOT modify objective_grader.py
- ✅ Did NOT modify web UI
- ✅ Did NOT modify dependency files
- ✅ Did NOT call real API
- ✅ Did NOT generate formal reports
- ✅ Did NOT commit local-test-materials
- ✅ Did NOT commit real teacher DOCX

## Available Pipeline
- JSON DocumentModel → extract_answer_key → validated answer key
- DOCX → parse_docx → extract_answer_key → validated answer key
- Synthetic DOCX generation + smoke testing
- Matrix v3 fixture validation

## Remaining Caveats
- Real Qwen API not yet connected
- Student answer card recognition not yet implemented
- Local real teacher DOCX smoke skipped (samples not available)
