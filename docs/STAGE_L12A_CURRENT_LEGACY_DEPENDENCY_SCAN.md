# Stage L12A — Current Legacy Dependency Scan

> Date: 2026-07-09
> Baseline commit: 74c3f9a

## workflow.py legacy status

- **imports legacy**: YES (`from legacy import objective_grader_legacy as legacy`)
- **Allowed calls (whitelisted)**: safe_slug, html_escape, ExamMeta, load_question_bank
- **Type annotations still using legacy types**: StudentResult, KnowledgeProfile, BankQuestion
- **Forbidden calls**: ALL removed — CSV writers, Excel writers, HTML writers, loaders, grading, builders, validation writer

## objective_grader.py legacy status

- **imports legacy**: YES (`from legacy import objective_grader_legacy as legacy`)
- **Allowed calls**: `create_sample_files` (for --make-samples and demo fallback)
- **COMPAT_EXPORTS**: 146 symbols re-exported via `globals().update()`
- **No star import**: confirmed

## app/domain legacy status

- **imports legacy**: NO

## app/application legacy status

- **imports legacy**: NO
- Exception: `csv_report_pipeline.py` bridges to infrastructure exporters (covered by architecture tests)

## app/infrastructure legacy status

- **imports legacy**: NO

## app/shared legacy status

- **imports legacy**: NO (directory may not exist yet)

## Other legacy importers in app/

| File | Imports legacy? | Why |
|------|----------------|-----|
| `app/validators.py` | YES | `build_validation_report`, `write_validation_report` |
| `app/analysis.py` | YES | Facade — re-exports legacy functions |
| `app/reports.py` | YES | Facade — re-exports legacy functions |
| `app/core.py` | YES | Facade — re-exports legacy functions |
| `app/workflow.py` | YES | safe_slug, html_escape, ExamMeta, load_question_bank |

## This round's targets

1. `app/validators.py` — can replace with application equivalent (or infrastructure writer)
2. `app/workflow.py` helper downshift — safe_slug, html_escape can use new shared helpers
3. `objective_grader.py` — can migrate create_sample_files to infrastructure
4. `COMPAT_EXPORTS` — audit and narrow

## Not targeted this round

- `app/analysis.py`, `app/reports.py`, `app/core.py` — facade files, defer to deletion readiness
- Legacy module itself — NOT deleting

## Why legacy is NOT deleted this round

Legacy still serves as:
1. Compatibility API for external scripts via objective_grader.py COMPAT_EXPORTS
2. Baseline for ~100+ tests
3. Fallback reference implementation
