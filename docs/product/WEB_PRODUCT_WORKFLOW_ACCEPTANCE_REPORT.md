# WEB-PRODUCT-WORKFLOW-R1-FIX1 Acceptance Report

## Acceptance decision

`APPROVED` for the FIX1 correctness scope. This is not approval for OCR/Qwen,
real-device or production operation.

## Correctness gates

| Gate | Evidence |
| --- | --- |
| Manual score bounds | Canonical QuestionSpec maximum; boolean, negative, non-numeric, non-finite, missing-question and over-max attacks rejected. |
| Database bypass | Finalization reloads and revalidates persisted resolutions; corrupted action/question/value keeps the gate blocked. |
| Final score | Publication validates finite score/max/percent and legal ranges before any formal record is committed. |
| Atomic publication | Injected artifact/publication failure leaves no final score, submission, artifact index or partial export. |
| Duplicate capture | Reasoned transaction sets exactly the duplicate jobs to `EXCLUDED`, preserves evidence, and publishes only originals. |
| Confirmation evidence | Snapshot is derived from persisted draft/review facts and stable IDs; missing/duplicate/order/open-review attacks block. |
| Benchmark oracle | Content comparison detects binding, score, max, percent, range, missing, unexpected and duplicate-result attacks. |
| Retired API | `/api/exams/grade` remains explicitly HTTP 410. |

## Deterministic benchmark truth

- Classes: 1
- Students: 50
- Capture jobs: 52
- Valid original captures: 50
- Duplicate captures: 2
- Excluded duplicate captures: 2
- Identity / answer / duplicate issues: 10 / 10 / 2
- Expected / actual final scores: 50 / 50
- Missing, unexpected, wrong binding, wrong score, wrong maximum, wrong percent,
  invalid range and wrong finalized: all 0

The processing-time p95 is measured afresh on each local run and is reported in
the generated benchmark JSON; it is not a correctness oracle.

## Boundaries verified

No dependency, OCR, Qwen, AI API, device watcher, EXE, cloud deployment, real
student data, real image or official learning report was added. No legacy or
canonical grading semantic was modified.
