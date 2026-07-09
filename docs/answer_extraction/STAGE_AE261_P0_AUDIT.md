# Stage AE261 P0 Audit

P0-1 bracket support status: fixed.

The itemized extractor now directly supports real `【答案】` forms, including same-line answers, colon variants, full-width dot/comma punctuation, and the split form where the question number is on one paragraph and `【答案】B` is on the next paragraph.

P0-2 evidence guard status: fixed.

`answer_key_validator.enforce_evidence_required` downgrades proposed `accepted` or `accepted_with_warnings` answers without evidence to `needs_review`. `evidence_invariant.enforce_result_evidence_invariant` also checks final engine output before returning safe JSON.

Fixture audit:

- v3 fixtures directly contain `【答案】`.
- expected_v3 files require evidence to contain `【答案】`.
- synthetic DOCX generator emits real `【答案】` paragraphs.

CLI audit:

- `--show-evidence` exposes evidence snippets.
- `--summary-only` can hide full answers without changing the internal invariant.
- local smoke remains skipped when no local samples exist.

Tests added:

- `tests/test_itemized_answer_extractor_chinese_bracket_p0.py`
- `tests/test_answer_key_validator_evidence_p0.py`
- `tests/test_answer_extraction_evidence_invariant.py`
- `tests/test_answer_extraction_v3_chinese_brackets_fixtures.py`
- `tests/test_answer_extraction_matrix_v3.py`
- synthetic DOCX generator and smoke tests
