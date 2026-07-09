# Stage AE521-AE560 Literal Real Bracket Fix — Summary

**Date:** 2026-07-09
**Stage:** AE521-AE560 Literal Real Bracket Fix and Anti-Shitshan Verification

## Objective

Make the code, fixtures, test assertions, CLI evidence, and docs all agree that the **real**
teacher answer marker is exactly `【答案】`, while `〖答案〗` / `[答案]` remain **compat-only**
markers that must never be called `real`.

## Five-Layer Consistency Verification

| Layer | Status | Evidence |
|-------|--------|----------|
| Code (`answer_markers.py`) | ✅ | `REAL_CHINESE_ANSWER_MARKER = "【答案】"`; `COMPAT_ANSWER_MARKERS = ("〖答案〗","[答案]")`; `build_answer_marker_regex()` built from `ANSWER_MARKERS`. |
| Code (`itemized_answer_extractor.py`) | ✅ | Imports `ANSWER_MARKER_RE` from `answer_markers`; no hardcoded `〖答案〗` regex; supports same-line and cross-block `【答案】`. |
| Fixtures | ✅ | All 11 `real*` fixtures contain `【答案】`, 0 `〖答案〗` (empirically counted). |
| Test assertions | ✅ | AE527 P0 test + AE526 named assertions + existing guards all assert `【答案】`. |
| CLI evidence (`--show-evidence`) | ✅ | `test_cli_real_chinese_brackets_evidence_p0.py` asserts at least one `evidence_text` contains `【答案】`; verified by running the CLI on `type2_same_file_itemized_with_real_chinese_brackets.json`. |
| Docs | ✅ | `ANTI_SHITSHAN_RULES.md` #11/#12 forbid `〖答案〗` in `real` files; no doc labels `〖答案〗` as the real marker. |

## What Changed This Round (in-scope, allowed files)

1. **AE527** — Created `tests/test_itemized_answer_extractor_real_chinese_brackets_p0.py`
   covering `1.【答案】B`, `1．【答案】B`, `1、【答案】B`, `1. 【答案】 B`, `1．【答案】：C`,
   `9．【答案】BD`, `12．【答案】\frac{1}{2}`, `13．【答案】x>1`, `14．【答案】[-1,2]`, and the
   cross-block `1.` / `【答案】B` form. Each asserts `【答案】` in `evidence_text` and does NOT
   contain a literal `〖答案〗` (uses `COMPAT_ANSWER_MARKERS[0]` for the negative check so the
   no-cosmetic-pass guard stays green).
2. **AE526** — Added the four spec-named assertions to `tests/test_answer_markers.py`:
   `test_real_chinese_answer_marker_is_literal_real_marker`, `test_real_marker_is_first_priority`,
   `test_compat_markers_do_not_include_real_marker`, `test_marker_regex_matches_real_and_compat_markers`.
3. **AE532** — Added `FIXTURE_NAMING_AUDIT_AE521.md` and this summary; confirmed no doc calls
   `〖答案〗` the real marker.

## Compat Preservation

- `〖答案〗` / `[答案]` still extracted (verified by `test_itemized_answer_extractor_compat_brackets.py`).
- Their `evidence_text` preserves the original compat marker; their test file is named `compat`.

## Evidence Invariant (AE533)

- `test_evidence_invariant_engine_output_p0.py` and `test_answer_extraction_no_evidence_accepted_guard_v3.py`
  pass: a candidate with no `evidence_text` cannot become `accepted`; `accepted_with_warnings`
  also requires evidence.

## Blocker — Commit/Push NOT completed

`python run_tests.py` and `python -m unittest discover` cannot pass because of a pre-existing
`NameError: name 'Any' is not defined` at `app/workflow.py:220`. `app/workflow.py` is in the
**forbidden modification list** and the task's stop conditions (#6, #17) require stopping rather
than modifying it. The answer-extraction bracket fix itself is verified correct and all
answer-extraction tests pass; only the grading-side suite is blocked by the forbidden-file bug.

See `STAGE_AE521_AE560_STOP_REPORT.md` for the stop decision and resolution options.
