# Stage L6 Report Archiver Status

Date: 2026-07-09

## Decision

No code migration was performed in L6.

`app/workflow.py` does not call `legacy.archive_reports`. The current workflow
uses its own `archive_exam_reports` helper, which differs from the legacy helper
by including `class_name` and `run_id` in the archive path and by writing richer
metadata. Migrating `legacy.archive_reports` into infrastructure and switching
workflow to it would therefore risk changing the current workflow archive
behavior.

## Current Calls

Static scan result:

- `legacy.archive_reports`: no active workflow call.
- `archive_exam_reports`: active workflow helper used when `archive_root` is set
  and `no_archive` is false.

## Boundary Notes

L6 was limited to checking whether the active workflow still depended on
`legacy.archive_reports`. Because it does not, no `app/infrastructure/archiving`
module was added in this L1-L6 round.

## Deferred Work

A future archive cleanup can:

- move `archive_exam_reports` from `app/workflow.py` to
  `app/infrastructure/archiving/report_archiver.py`,
- preserve the current run-id-aware archive directory structure,
- add parity tests for the active workflow archive behavior rather than parity
  against `legacy.archive_reports`,
- then remove archive implementation details from workflow.

Legacy itself remains unchanged and available as a frozen baseline.
