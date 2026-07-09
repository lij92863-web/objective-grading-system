# Stage L12 Legacy Dependency Guard Matrix

## Guard Scope

The L12 guard matrix records the current allowed and forbidden legacy
dependencies after the L7-L11 cutovers.

## Workflow

Forbidden direct `legacy.*` calls in `app/workflow.py`:

- CSV writers: `write_summary`, `write_detail`, `write_item_analysis`,
  `write_knowledge_profiles`, `write_practice_recommendations`,
  `write_class_report`, `write_validation_report`, `write_student_report`
- Excel writers: `write_workbook`, `write_simple_score_workbook`,
  `write_enhanced_workbook`
- HTML writers: `write_simple_report`, `write_advanced_dashboard`,
  `write_report_index`
- analysis helpers: `simple_score_rows`, `item_stats`
- CSV loaders: `load_answer_key`, `load_submissions`
- grading: `grade_all`
- report builders: `build_validation_report`, `build_knowledge_profiles`,
  `basic_stats`

Allowed workflow legacy dependencies remain:

- `safe_slug`
- `html_escape`
- `ExamMeta`
- `load_question_bank`

These are intentionally left for later deletion-readiness work.

## Layers

Forbidden imports:

- `app/application/**` must not import `legacy` or `web`.
- `app/application/**` must not import infrastructure exporters.
  Existing exception: `app/application/use_cases/csv_report_pipeline.py` is an
  orchestration bridge to CSV exporters and is covered by the existing
  architecture tests.
- `app/infrastructure/**` must not import `legacy` or `web`.
- `app/domain/**` must not import `legacy`, infrastructure, or `web`.

## CLI

`objective_grader.py` may still import the legacy module only for:

- explicit compatibility exports through `COMPAT_EXPORTS`;
- direct `legacy.create_sample_files(...)` calls for sample/demo input files.

Forbidden in `objective_grader.py`:

- star import from legacy;
- direct calls to legacy loaders, report writers, grading core, or analysis
  builders.

## Tests

`tests/test_legacy_dependency_guard_matrix.py` enforces this matrix with AST
checks.
