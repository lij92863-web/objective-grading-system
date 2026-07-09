# AE421 P0 Bracket Audit

**Date:** 2026-07-09

## Audit Results

| # | Check | Result |
|---|-------|--------|
| 1 | itemized_answer_extractor.py 是否直接包含【答案】支持 | PASS |
| 2 | text_normalizer.py 是否把【】转换成其它括号 | PASS (no conversion) |
| 3 | real_chinese_brackets fixture 是否真的含【答案】 | PASS |
| 4 | real_chinese_brackets test 是否真的断言【答案】 | PASS |
| 5 | synthetic DOCX generator 是否真的生成【答案】 | PASS |
| 6 | CLI --show-evidence 是否输出【答案】 | PASS |

## Evidence

1. **itemized_answer_extractor.py** line 21: regex includes `【答案】` via `ANSWER_MARKER_RE` from `answer_markers.py`
2. **text_normalizer.py**: NFKC normalize only, no bracket conversion
3. **v3 fixtures**: `type2_same_file_itemized_with_real_chinese_brackets.json` contains 【答案】=4, 〖答案〗=0
4. **test_itemized_answer_extractor_chinese_bracket_p0.py** line 23: `assertIn("【答案】", candidate.evidence_text)`
5. **scripts/generate_answer_extraction_synthetic_docx.py**: generates `1.【答案】B`, `2．【答案】C`
6. **CLI**: `--show-evidence` outputs evidence_text containing 【答案】

## Structural Improvements (AE421-AE520)
- Created `answer_markers.py` (centralized marker definitions)
- Created `status_model.py` (centralized status constants)
- Updated `itemized_answer_extractor.py` to use `ANSWER_MARKER_RE`
- Updated `answer_key_validator.py` to use status constants
- Updated `evidence_invariant.py` to use status constants
