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
