# WEB-PRODUCT-WORKFLOW-R1-FIX1 CTO Review

## Decision

**APPROVED**

FIX1 closes the identified correctness gaps in the local synthetic workflow:
manual scores have a canonical server-side maximum, formal scores have final
range invariants, duplicate captures have an audited exclusion path,
confirmation evidence is derived from persisted facts, and benchmark success
is based on content truth rather than row count.

This approval is limited to FIX1. It is not authorization for real devices,
real student material, OCR, Qwen, cloud deployment or production use.

## Findings

| Review question | Finding |
| --- | --- |
| Can a manual score exceed the question maximum? | No. Review and finalization both use `ManualScorePolicy` with canonical `QuestionSpec.points`; no clamp exists. |
| Can database tampering bypass review validation? | No. The gate reloads and validates every persisted resolution and its session/job association. |
| Can a formal score exceed its maximum or 100%? | No. The publication boundary rejects non-finite and out-of-range rows atomically. |
| Can a duplicate capture be handled honestly? | Yes. It is explicitly excluded with a reason, full resolutions and append-only audit; evidence is retained. |
| Does an excluded capture publish a score? | No. It is absent from confirmed submissions, final submissions and final scores. |
| Is confirmation evidence fabricated? | No. Snapshot fields come from persisted capture, draft, evidence, issue and resolution facts plus confirmation audit. |
| Can order changes misassociate a draft? | No. Stable IDs are used and missing/duplicate mappings block. |
| Does the benchmark validate content? | Yes. An independent oracle checks identity, score, maximum, percent, ranges, missing/unexpected and duplicate rows. |
| Is the old direct-grade API restored? | No. `/api/exams/grade` remains HTTP 410. |

## Adversarial evidence

The adversarial regression audit executes counterfactual tests for negative,
boolean, non-finite, over-max and wrong-question scores; direct database
corruption; unresolved and excluded duplicates; missing/duplicate/reordered
snapshot mappings; score/export publication failure; and benchmark result
tampering. Static product audits additionally reject the former fabricated
empty snapshot, positional draft/submission coupling and count-only oracle.

## Benchmark finding

The deterministic benchmark uses 50 students, 50 valid original captures and 2
duplicate captures. It produces 10 identity, 10 answer and 2 duplicate issues.
Both duplicates finish as `EXCLUDED`; 50 expected records match 50 actual formal
scores with zero missing, unexpected, binding, numeric, range or finalized
errors. Runtime p95 is informative only and is never used to establish score
correctness.

## Remaining boundaries

- Real-image recognition accuracy and physical-device behavior are untested.
- The application remains local and single-user without production security or
  deployment claims.
- No OCR/Qwen, new dependency, watcher, EXE or formal analytics report was added.

These boundaries do not block FIX1 because they are explicitly outside its
scope. The next phase was not entered as part of this task.
