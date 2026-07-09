# Anti-Shitshan Rules

These rules prevent cosmetic passes that claim functionality without delivering it.

## Rules

1. **Triple Evidence for Reports**: When a report claims support for feature X, there must be code, fixture, and test assertion triple evidence.

2. **Name-Content-Assertion Consistency**: A file named `real_chinese_brackets` MUST contain `【答案】` in its data. A test named `real_chinese_brackets` MUST assert `【答案` in evidence text.

3. **Extractor Only Produces Candidate**: All extractors (`extract_answer_tables`, `extract_itemized_answers`) must only produce `AnswerCandidate` objects. They must not directly set `accepted`/`accepted_with_warnings`/`blocked` statuses.

4. **Final Status Centralized**: Final answer statuses must only be set by `AnswerKeyValidator`, `EvidenceInvariant`, and `CandidateConflictResolver`.

5. **Evidence Required for Acceptance**: Any `accepted` or `accepted_with_warnings` answer must have non-empty `evidence_text`, `source_kind`, `source_file`/`source_document_id`, and `source_block_id`/`source_table_id`/`source_span`.

6. **Confidence from Policy**: `confidence` values must come from `answer_source_policy.confidence_for_source()`. No magic number confidence assignments.

7. **Status from Model**: Status strings must use constants from `status_model.py`. No bare string literals for `"accepted"`, `"accepted_with_warnings"`, etc.

8. **No Relaxing Blocking for Samples**: Don't relax blocking rules just to make samples pass.

9. **Skipped ≠ Verified**: When `local smoke` is skipped due to missing samples, don't claim real DOCX has been verified.

10. **Regression Test Required**: Every historical bug must have a regression test.

11. **Real Chinese Brackets**: `real_chinese_brackets` files MUST use `【答案】`. Using `〖答案〗` in a file named `real` is a shitshan pattern.

12. **Compat Brackets Named Accordingly**: Files testing `〖答案〗` or `[答案]` compatibility must have `compat` in their name, never `real`.

## Guard Tests

The following guard tests enforce these rules automatically:
- `test_answer_extraction_fixture_truthfulness_guard.py`
- `test_answer_extraction_no_cosmetic_pass_guard.py`
- `test_answer_extraction_status_model_guard.py`
- `test_answer_source_policy_usage_guard.py`
- `test_evidence_invariant_engine_output_p0.py`
- `test_cli_real_chinese_brackets_evidence_p0.py`
- `test_synthetic_docx_real_brackets_p0.py`
