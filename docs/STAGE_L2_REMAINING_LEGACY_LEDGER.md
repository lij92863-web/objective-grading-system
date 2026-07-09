# Stage L2 Remaining Legacy Ledger

Date: 2026-07-09

## Scope

This ledger records the legacy dependencies still visible after the E4 HTML
exporter migration and before the L3-L6 shrink work. The current long-run task
is L1-L6, so CSV loader and CLI compatibility changes are deferred unless they
are required by L1-L6.

## Current Main-Chain Legacy Imports

`app/workflow.py` still imports `legacy.objective_grader_legacy as legacy`.
The active uses are:

- Compatibility/data contracts: `StudentResult`, `KnowledgeProfile`,
  `BankQuestion`, `ExamMeta`.
- Core grading path: `load_answer_key`, `load_submissions`, `grade_all`,
  `build_knowledge_profiles`, `load_question_bank`,
  `build_validation_report`, `basic_stats`.
- Error-path CSV writer: `write_validation_report`.
- Small helpers: `safe_slug`, `html_escape`.
- Analysis rows for Excel/HTML: `simple_score_rows`, `item_stats`.

`objective_grader.py` still imports legacy in two ways:

- `from legacy.objective_grader_legacy import *` keeps the historical public
  CLI module compatibility API.
- `from legacy import objective_grader_legacy as legacy` is used for
  `create_sample_files` in `--make-samples` and built-in demo mode.

## Legacy Used By Baseline Tests

Many migration tests still import legacy as a behavioral oracle. Those imports
are acceptable in tests because they compare new application/infrastructure
implementations with the frozen legacy baseline. Examples include CSV, Excel,
HTML exporter parity tests and report builder parity tests.

## Compatibility / Re-export Surface

The compatibility facade currently remains in:

- `objective_grader.py`, via star import.
- `app/core.py` and `app/reports.py`, as documented architecture exceptions.
- Tests that assert compatibility behavior.

This stage does not remove that facade.

## Functions Prepared For This Round

The L1-L6 round is prepared to move or route:

- `simple_score_rows` through `app.application.use_cases.report_builders`.
- `item_stats` through `app.application.use_cases.report_builders`.
- `archive_reports` only if the active workflow uses the legacy archive
  helper.

## Functions Deferred

The following are explicitly deferred beyond L1-L6:

- `load_answer_key`
- `load_submissions`
- `objective_grader.py` legacy compatibility import cleanup
- full workflow removal of all legacy imports
- legacy deletion

## Archive Status

`app/workflow.py` does not call `legacy.archive_reports`. It uses its own
`archive_exam_reports`, with run-id-aware archive directory names. Because the
active workflow does not use `legacy.archive_reports`, L6 should document this
status instead of migrating archive code.

## Why Legacy Is Not Deleted In This Round

Legacy remains the baseline and compatibility surface for:

- behavior parity tests,
- CLI public symbol compatibility,
- core grading functions not yet migrated in L1-L6,
- sample file generation,
- historical app facades.

Deleting or editing legacy would make it impossible to prove parity for this
round and would exceed the task boundary.

## Next Quarantine Candidates

After L1-L6, the next candidates are:

- migrate CSV loaders into `app.infrastructure.loaders`,
- shrink `objective_grader.py` to a pure CLI entry while preserving an explicit
  compatibility route,
- replace `workflow.py` loader/helper calls with non-legacy infrastructure and
  helper modules,
- add a unified legacy call guard matrix for workflow and CLI entrypoints,
- then reassess whether compatibility facades can be quarantined or removed.
