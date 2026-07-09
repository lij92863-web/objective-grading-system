# AE261 P0 Audit

**Date:** 2026-07-09

## P0-1: `【答案】` Bracket Support Status

### Regex Audit
- `itemized_answer_extractor.py` line 21: PATTERNS regex already includes `【答案】` alongside `〖答案〗` and `[答案]`
- `itemized_answer_extractor.py` line 37: INLINE_WITHOUT_QNO also includes `【答案】`
- **Verdict: ALREADY SUPPORTED** — The regex `(?:【答案】|〖答案〗|\[答案\])` covers all three brackets.

### Fixture Audit
- v2 fixtures: `type2_same_file_itemized_with_chinese_brackets.json` already uses `【答案】` (not just `〖答案〗`)
- v3 fixtures: `type2_same_file_itemized_with_real_chinese_brackets.json` uses `【答案】` exclusively, no `〖答案〗`
- **Verdict: ALREADY COVERED** — both v2 and v3 fixtures test `【答案】`.

### CLI Verification
```
python scripts/extract_answer_key.py --file ...v3/type2_same_file_itemized_with_real_chinese_brackets.json --json --show-evidence
→ status: accepted, source_kind: explicit_bracket_answer, evidence contains 【答案】
```

## P0-2: Evidence Guard Status

### Validator Audit
- `answer_key_validator.py` line 28-33: `enforce_evidence_required()` exists
  - Checks `proposed_status in {"accepted", "accepted_with_warnings"}` AND `not candidate.evidence_text`
  - Downgrades to `needs_review` with `missing_evidence_for_accepted_answer`
- Called at line 73 for every validated answer
- **Verdict: IMPLEMENTED CORRECTLY**

### Engine-Level Audit
- `extraction_engine.py` line 206: `enforce_result_evidence_invariant()` applied post-processing
- `evidence_invariant.py`: validates accepted answers have evidence_text, source_kind, source_file, source_span
- **Verdict: DOUBLE-GUARDED** — validator + invariant post-processing

### Evidence Sources
- Table answers: `f"题 {question_no} 答 {raw}"` — always non-empty
- Itemized answers: `block.text` or concatenated block text — always set
- **Verdict: ALL EXTRACTORS PROVIDE EVIDENCE**

## Fix Plan
Both P0s are already addressed by existing code. Remaining work:
1. Add explicit `【答案】` unit tests even though regex supports it (AE262)
2. Add evidence guard unit tests for edge cases (AE263)
3. Complete remaining AE tasks per CODEX_TASK

## Tests to Add
- `test_itemized_answer_extractor_chinese_bracket_p0.py` — 18 tests for `【答案】` patterns
- `test_answer_key_validator_evidence_p0.py` — evidence guard unit tests
