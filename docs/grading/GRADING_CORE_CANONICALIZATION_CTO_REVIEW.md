# GRADING-CORE-CANONICALIZATION-R1 CTO Review

## Decision

**APPROVED_WITH_CAVEATS**

The deterministic grading core now has one formal model source, one grading
normalizer, one question-type protocol, and one precheck gate. Blocking input
returns validation/error artifacts without invoking `grade_all`. The legacy
`run_grading(...)` signature remains only as a compatibility and report adapter;
the application core accepts `GradingRunRequest` and returns
`GradingRunResult`.

## Release questions

| Question | Finding |
| --- | --- |
| One formal domain model set? | Yes: `app/domain/grading/models.py`; the CSV loader imports these classes. |
| One grading `normalize_answer`? | Yes: `app/domain/grading/normalize.py`. Recognition/answer-extraction normalization is a separately bounded subsystem and was not modified. |
| Does every formal file-workflow grade pass precheck first? | Yes: the wrapper delegates to the typed orchestrator, which returns before `grade_all` when blocked. |
| Can `allow_errors=True` bypass a core error? | No. It emits a deprecation warning and has no gate authority. |
| Are valid historical scores compatible? | Yes: benchmark score parity and question-detail parity are both 100%. |
| Does a caller still depend on loader-private models? | No private loader models remain. Compatibility imports resolve to canonical instances. |
| Does report validation duplicate input blocking rules? | No. Its duplicate identity/question and invalid-status blockers were removed; it only emits post-grade/display observations. |
| New circular dependency? | No. Domain has no infrastructure/workflow/web imports; loader and application point inward to domain. |
| SRE, recognition, web, or grading exporters modified? | No. |

## Security and adversarial results

- Empty expected answers, unknown types/statuses, ambiguous bare `T/F/X`,
  conflicting duplicate questions, duplicate student identities, missing
  submissions, and external blocking validation issues fail closed.
- Identical duplicate questions are deduplicated with a warning while source
  rows and raw answer/point/type evidence remain available.
- `Submission.answers` and `Submission.raw_answers` copy their inputs and expose
  read-only mappings.
- `A1` remains an invalid token; it is never guessed to be `A`.
- Overrides require actor, reason, creation time and known codes. Core model,
  identity, type/status, draft and answer-key conflicts are non-overridable.
- Legacy result adaptation preserves raw, student, normalized and tokenized
  answer fields independently.

## Caveats and deferred work

- `run_grading(...)` still returns its historical dictionary for CLI/UI
  compatibility. New application code must use the typed orchestrator.
- The report pipeline consolidation, fully typed report rows, and broad input
  parser hardening remain explicitly deferred.
- The recognition ownership question remains `UNRESOLVED_BOUNDARY`; the safe
  confirmed-submission-to-canonical-submission adapter direction is documented,
  but no recognition code was changed in this release.

These caveats do not weaken the grading gate. REPORT-PIPELINE-CONSOLIDATION-R1
may begin only as a separate authorized phase; this review does not start it.
