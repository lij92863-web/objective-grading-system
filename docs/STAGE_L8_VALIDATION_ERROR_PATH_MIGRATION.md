# Stage L8 Validation Error Path Migration

## L8A Audit

`app/workflow.py` still calls `legacy.write_validation_report` in the
temporary output directory before it checks the blocking-error branch. This is
the only remaining workflow CSV writer call that is intentionally outside the
normal CSV pipeline.

Current error-path trigger:

- `validation_rows = legacy.build_validation_report(...)` is built during
  orchestration.
- `extra_validation_rows` are appended.
- `has_blocking_errors(validation_rows)` decides whether the run is blocked.
- A blocking row has severity `error` or `blocking`, and either an empty scope
  or a scope in `app.validators.BLOCKING_SCOPES`.
- `legacy.write_validation_report(temp_dir / "validation_report.csv",
  validation_rows)` runs before the blocked branch returns.
- If blocked and `allow_errors` is false, workflow writes `error_report.html`,
  replaces report outputs atomically, and returns `ok=False`.

Legacy writer behavior:

- Output filename in workflow: `validation_report.csv`.
- Function: `legacy.write_validation_report(path, rows)`.
- Implementation delegates to `write_dicts_with_fields`.
- Field order: `severity`, `scope`, `item`, `message`.
- Encoding: `utf-8-sig`.
- Newline mode: `newline=""`.
- Empty rows: header-only CSV.
- Input shape: `List[Dict[str, object]]`.

Existing replacement candidate:

- `app/infrastructure/exporters/validation_report_csv_exporter.py` already
  provides `ValidationReportCsvExporter`.
- It uses the same field order and `write_dict_rows_csv`, which also uses
  `utf-8-sig` and creates parent directories.
- It writes only pre-computed rows and does not rebuild validation business
  data, so it is an infrastructure replacement for the writer call.

Why the exemption existed:

- Earlier CSV exporter work routed the normal success-path CSV files through
  the pipeline, while this writer remains before the blocking branch so failed
  runs can still emit `validation_report.csv`.

Migration risk:

- The replacement must preserve the blocking branch's output filename, field
  order, BOM encoding, and header-only behavior for empty rows.
- It must not change the trigger conditions, generated `error_report.html`, or
  normal success-path reports.

L8A conclusion: this path is safe to migrate to the existing
`ValidationReportCsvExporter` after parity tests cover both direct writer output
and workflow blocked output.

