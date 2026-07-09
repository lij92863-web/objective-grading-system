# Answer Extraction Regression Matrix V3

V3 closes the two P0 issues from v2: direct real `【答案】` support and a final evidence invariant for accepted answers.

Covered risks:

- Real `【答案】` same-line and split-paragraph answers.
- Complex fill-blank answers such as `\frac{1}{2}`, `x>1`, and intervals.
- Empty student answer grids never becoming standard answer keys.
- Segmented answer tables and vertical answer tables.
- Years and analysis step markers not becoming question IDs.
- Missing answers remain missing/review.
- Unexpected answer numbers block.
- Duplicate conflicting answers block.
- Single-choice multi-answer blocks.
- LLM candidates are never directly accepted.
- Accepted and accepted-with-warnings answers require evidence.

Primary tests:

- `tests/test_itemized_answer_extractor_chinese_bracket_p0.py`
- `tests/test_answer_key_validator_evidence_p0.py`
- `tests/test_answer_extraction_evidence_invariant.py`
- `tests/test_answer_extraction_matrix_v3.py`
- `tests/test_run_answer_extraction_synthetic_docx_smoke.py`

Remaining caveat: generated synthetic DOCX is intentionally minimal. It validates parser and extraction behavior without representing every possible Word layout feature.
