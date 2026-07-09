# Stage B1 — Test Legacy Baseline Scan

## Tests with actual legacy import: 26 files

They import legacy for "new vs legacy" comparison (baseline oracle).

## Tests with text-only legacy mentions: 43 files
Guard tests, docs references, architecture checks — no runtime legacy dependency.

## Categories (B2)
- **A (replace with fixtures)**: report builders, loaders, exporters, parity, grading baseline
- **B (keep for compat)**: compat export parity, objective_grader compat module, legacy entrypoints import
- **C (text-only, fine)**: guard/deletion/dependency/architecture tests
