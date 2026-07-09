# Stage AE521-AE560 Preflight

**Date:** 2026-07-09
**Operator:** GStack 工程团队（主理人沽思航）

## Environment

| Item | Value |
|------|-------|
| 当前分支 | main |
| 当前 commit | a779fc1 (fix add real chinese answer bracket support with anti-shitshan structural guards) |
| git status (before edits) | clean (no uncommitted changes) |
| Python | managed 3.13 |

## Preflight Test Results

| Command | Result | Note |
|---------|--------|------|
| `python run_tests.py` | ❌ FAIL (import) | `app/workflow.py:220` → `NameError: name 'Any' is not defined`. `app/workflow.py` imports `from typing import Dict, Iterable, List, Optional, Tuple` (no `Any`) but uses `List[Any]` at lines 220 and 309. No `from __future__ import annotations`. |
| `python -m unittest discover` | ❌ FAIL | 111 errors + 6 failures. All cascade from the same `app.workflow` `Any` NameError (any test module that imports `objective_grader` / `app.workflow` crashes at import). |
| `python -m unittest <answer_extraction modules>` | ✅ PASS | 54 tests across `test_answer_markers`, `test_itemized_answer_extractor_real_chinese_brackets_p0`, `test_answer_extraction_fixture_truthfulness_guard`, `test_answer_extraction_no_cosmetic_pass_guard`, `test_cli_real_chinese_brackets_evidence_p0`, `test_itemized_answer_extractor_compat_brackets`, `test_evidence_invariant_engine_output_p0`, `test_answer_extraction_no_evidence_accepted_guard_v3` all pass. |

## Root-Cause of Preflight Failure

- The failure is **not** in the answer-extraction bracket code. It is a pre-existing
  `NameError` in `app/workflow.py` (a **forbidden-to-modify** file per the task rules).
- `app/workflow.py` is imported transitively by `objective_grader` and by many grading-side
  test modules, so the whole suite crashes at import time.
- The answer-extraction modules (`app/answer_extraction/**`) and their tests do **not**
  import `app.workflow`, therefore they run and pass independently.

## 本轮 P0 问题

**Literal real bracket mismatch.** The real teacher marker must be exactly `【答案】`.
The previous round (a779fc1) already set `REAL_CHINESE_ANSWER_MARKER = "【答案】"` in
`app/answer_extraction/answer_markers.py`, and all `real_chinese_brackets` / `real_brackets`
fixtures, tests, and the synthetic DOCX generator already use `【答案】` (verified:
0 occurrences of `〖答案〗` in any `real*` fixture). Compat markers `〖答案〗` / `[答案]`
are preserved only under `COMPAT_ANSWER_MARKERS` and under `compat`-named files/tests.

The remaining gaps filled in this round:
1. Created `tests/test_itemized_answer_extractor_real_chinese_brackets_p0.py` (AE527) — the
   missing P0 extraction test asserting `【答案】` appears in `evidence_text`.
2. Added the four spec-named assertions to `tests/test_answer_markers.py` (AE526).
3. Added `FIXTURE_NAMING_AUDIT_AE521.md` and `STAGE_AE521_AE560_LITERAL_BRACKET_FIX_SUMMARY.md`
   (AE532) and confirmed no doc labels `〖答案〗` as the real marker.

## Blocker (see STOP report)

Commit + push cannot be completed because `python run_tests.py` / `python -m unittest discover`
cannot pass without fixing the forbidden file `app/workflow.py`. Per the task's stop conditions
(#6 modify workflow.py, #17 run_tests.py fails and cannot be fixed), this round is **STOPPED**.
See `STAGE_AE521_AE560_STOP_REPORT.md`.
