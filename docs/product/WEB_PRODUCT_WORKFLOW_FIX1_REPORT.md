# WEB-PRODUCT-WORKFLOW-R1-FIX1 Repair Report

## Scope and starting point

- Actual starting commit: `eda6c444e5394fe557dc14df2b6a31607723b20d`.
- This is a correctness repair to the local synthetic product workflow. It does
  not add OCR, Qwen, device integration, dependencies, real images, real rosters
  or an official analytics report.
- Legacy grading entry points and canonical grading semantics were not changed.

## Root causes and repairs

### Manual scores

The review service previously checked only that a score existed and was not
negative. It did not use the canonical question maximum, reject booleans and
non-finite values, or defend finalization against direct database tampering.
Older happy-path tests therefore did not exercise over-max, NaN/Inf or database
bypass cases.

`ManualScorePolicy` is now the single authority used by review, finalization
gate and score construction. It resolves `QuestionSpec` through the canonical
`AnswerKey.by_number`, rejects invalid action/score combinations and requires a
finite value in `[0, QuestionSpec.points]`. It never clamps. The review page
shows that same canonical maximum with `min="0"`, `max` and `step="any"`; this is
only a usability aid and not a security boundary.

### Final-score invariants and atomicity

The gate reloads every persisted resolution and validates its session, capture
job, action, question and score. The publication layer separately validates
finite `score`, `max_score` and `percent`, including the zero-maximum case and
the ranges `[0,max_score]` and `[0,100]`. Any failure aborts the transaction,
removes staged/published partial files and leaves final submissions, scores,
artifacts and session state unpublished. Invalid values are rejected rather
than silently corrected.

### Duplicate captures

An identity review now has an explicit reason-required “exclude capture”
operation. One transaction closes every open issue on that capture with a
resolution, appends audit evidence and changes the capture job to `EXCLUDED`.
The original image reference, RecognitionDraft, evidence and history are kept.
Excluded jobs do not create confirmed submissions, final submissions or final
scores. Closed issues, missing issues, already-published sessions and partial
transaction failures are fail-closed.

### Confirmation evidence

The former hard-coded empty `draft_snapshot` and positional `zip` association
were removed. `ConfirmedSubmissionBuilder` now reads the persisted capture job,
RecognitionDraft evidence/provisional payload, issue state and complete review
resolution history. It also uses the persisted teacher-confirmation actor and
time. Drafts and grading submissions are associated by stable job/student IDs.
Missing or duplicate drafts, missing mappings, open reviews and closed issues
without resolution evidence produce blockers. Excluded jobs are omitted.

### Benchmark truth

The deterministic fixture now contains 50 students, 50 valid original captures
and 2 duplicate captures. It creates 10 identity issues, 10 answer issues and 2
duplicate-identity issues. The duplicates are excluded, not rebound.

Expected score truth is built from the known roster and fixture before final
results exist. `product_workflow_oracle.py` compares student ID, number, name,
score, maximum and percent, checks ranges, detects missing/unexpected and
duplicate rows, and computes `wrong_finalized_count` from content errors. Tests
deliberately tamper student number, score, swapped scores, row presence, range
and duplication; every attack is detected.

## Residual caveats

No FIX1 correctness caveat remains in the synthetic local workflow. Existing
boundaries remain: no real-image recognition claim, no physical-device
validation, no multi-user security, and no production authorization. Those are
future stages and were not entered here.
