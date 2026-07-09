# Fixture Naming Audit AE421

**Date:** 2026-07-09

## Modified Real Bracket Fixtures (content confirmed 【答案】)
All v3 `real_chinese_brackets` fixtures already use `【答案】`:
- `document_models_v3/type2_same_file_itemized_with_real_chinese_brackets.json` ✅
- `document_models_v3/type4_answer_itemized_real_chinese_brackets.json` ✅
- `document_models_v3/type2_same_file_itemized_fill_blank_real_brackets.json` ✅
- `matrix_v3/04_same_file_itemized_real_brackets.json` ✅
- `matrix_v3/10_split_itemized_real_brackets_answer.json` ✅
- `synthetic_docx_v3/same_file_itemized_real_brackets.docx` ✅
- `synthetic_docx_v3/split_answer_itemized_real_brackets.docx` ✅

## Compat Bracket Fixtures (still use 〖答案〗 / [答案])
v2 fixtures use 〖答案〗 but are NOT named `real`:
- `document_models_v2/type2_same_file_itemized_with_chinese_brackets.json` — contains 【答案】 (already correct)

## Tests Asserting 【答案】
- `test_itemized_answer_extractor_chinese_bracket_p0.py` line 23: `assertIn("【答案】", candidate.evidence_text)`
- `test_cli_real_chinese_brackets_evidence_p0.py`: asserts CLI output contains 【答案】
- `test_synthetic_docx_real_brackets_p0.py`: asserts DOCX text contains 【答案】
- `test_answer_extraction_fixture_truthfulness_guard.py`: scans all files for truthfulness
- `test_answer_extraction_no_cosmetic_pass_guard.py`: prevents cosmetic passes

## Compat Tests Retained
- `test_itemized_answer_extractor_compat_brackets.py`: tests 〖答案〗 / [答案] still work
