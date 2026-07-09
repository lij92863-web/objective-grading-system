# Fixture Naming Audit AE521

**Date:** 2026-07-09

## Rule (Anti-Shitshan #11 / #12)

- `real_chinese_brackets` / `real_brackets` files MUST use `【答案】`.
- Using `〖答案〗` inside a file/name that claims to be `real` is a shitshan (cosmetic-pass) pattern.
- Files that exercise `〖答案〗` / `[答案]` compatibility MUST carry `compat` in their name.

## Real Bracket Fixtures (content confirmed `【答案】`, zero `〖答案〗`)

| Fixture | `【答案】` | `〖答案〗` |
|---------|-----------|-----------|
| document_models_v3/type2_same_file_itemized_with_real_chinese_brackets.json | 4 | 0 |
| document_models_v3/type4_answer_itemized_real_chinese_brackets.json | 4 | 0 |
| document_models_v3/type2_same_file_itemized_fill_blank_real_brackets.json | 4 | 0 |
| expected_v3/type2_real_brackets_expected.json | 1 (`expected_evidence_contains`) | 0 |
| expected_v3/type4_real_brackets_expected.json | 1 | 0 |
| expected_v3/type2_fill_blank_real_brackets_expected.json | 1 | 0 |
| matrix_v3/04_same_file_itemized_real_brackets.json | 4 | 0 |
| matrix_v3/10_split_itemized_real_brackets_answer.json | 4 | 0 |
| matrix_v3/10_split_itemized_real_brackets_question.json | 0 (question only) | 0 |
| synthetic_docx_v3/same_file_itemized_real_brackets.expected.json | 0 (companion) | 0 |
| synthetic_docx_v3/split_answer_itemized_real_brackets.expected.json | 0 (companion) | 0 |

All `expected_evidence_contains` values use `"【答案】"`, not `"〖答案〗"`.

## Compat Bracket Fixtures (use `〖答案〗` / `[答案]` only under `compat` naming)

- `test_itemized_answer_extractor_compat_brackets.py` — tests `〖答案〗` / `[答案]` still work
  and asserts their `evidence_text` preserves the original compat marker. File name contains
  `compat`, so it is correctly NOT named `real`.
- No `real*`-named fixture contains `〖答案〗`.

## Tests Asserting `【答案】`

- `tests/test_answer_markers.py` — `test_real_chinese_answer_marker_is_literal_real_marker`,
  `test_real_marker_is_first_priority`, `test_compat_markers_do_not_include_real_marker`,
  `test_marker_regex_matches_real_and_compat_markers`.
- `tests/test_itemized_answer_extractor_real_chinese_brackets_p0.py` — NEW this round; asserts
  `【答案】` in `evidence_text` for 9 same/cross-block forms. Contains NO literal `〖答案〗`.
- `tests/test_cli_real_chinese_brackets_evidence_p0.py` — asserts CLI output contains `【答案】`.
- `tests/test_answer_extraction_fixture_truthfulness_guard.py` — scans every `real*` file for
  truthfulness (`【答案】` present, `〖答案〗` absent).
- `tests/test_answer_extraction_no_cosmetic_pass_guard.py` — prevents renaming-only cosmetic
  passes (real-named files must contain `【答案】` and must not contain literal `〖答案〗`).

## Verdict

✅ All `real*` fixtures, expected files, and real-named tests are consistent with the literal
real marker `【答案】`. No `〖答案〗` is masquerading as a real marker anywhere in the
answer-extraction corpus.
