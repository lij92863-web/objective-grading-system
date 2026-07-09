# Stage L11 CLI Legacy Shrink

## L11A Audit

`objective_grader.py` currently has three responsibilities:

- define CLI arguments;
- create sample/demo input CSVs when requested or when no input is supplied;
- delegate grading/report generation to `app.workflow.run_grading`.

Current legacy imports:

- `from legacy.objective_grader_legacy import *`
- `from legacy import objective_grader_legacy as legacy`

Current direct legacy calls:

- `legacy.create_sample_files(args.out_dir)` for `--make-samples`;
- `legacy.create_sample_files(demo_dir)` for the built-in demo path.

Current non-legacy main path:

- `run_grading(...)` from `app.workflow`.

Compatibility API:

- The star import preserves older scripts/tests that imported legacy public
  symbols from `objective_grader.py`.
- Removing it without a compatibility export list would be a behavior change.

Can be removed now:

- Direct use of legacy loaders/report writers/grading in the CLI main path:
  none remain.

Candidate for L11B:

- Replace the star import with an explicit compatibility whitelist, if current
  tests and downstream expectations can be kept stable.
- Keep `legacy.create_sample_files` unless a small sample writer already exists
  outside legacy. Copying large sample/demo code into `objective_grader.py` is
  not acceptable.

L11A conclusion: `objective_grader.py` can likely shrink from a star import to
an explicit whitelist while preserving `legacy.create_sample_files` as the only
direct legacy call for sample/demo compatibility.

## L11B Shrink

`objective_grader.py` no longer uses:

- `from legacy.objective_grader_legacy import *`

It now keeps a `COMPAT_EXPORTS` tuple and explicitly re-exports those names
from `legacy.objective_grader_legacy`. This preserves the previous compatibility
surface without using a star import.

Direct legacy calls remaining in the CLI:

- `legacy.create_sample_files(...)` for `--make-samples`;
- `legacy.create_sample_files(...)` for the no-input built-in demo.

No direct calls remain in `objective_grader.py` to legacy loaders, report
writers, grading core, or analysis builders.

Guard coverage:

- `tests/test_objective_grader_legacy_dependency_guard.py` forbids the legacy
  star import and allows only `create_sample_files` direct legacy calls.
- `tests/test_cli_compatibility_exports.py` verifies common compatibility
  exports, CLI options, and `--make-samples` still work.

No CLI arguments or report output formats were changed.
