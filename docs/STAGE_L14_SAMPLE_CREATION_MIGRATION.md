# Stage L14 — Sample Creation Migration

## Result: Migrated

`create_sample_files` moved from `legacy.objective_grader_legacy` to `app/infrastructure/samples/sample_files.py`.

### Output files (unchanged)
- `answer_key_sample.csv` (3 questions, UTF-8-BOM)
- `submissions_sample.csv` (2 students, UTF-8-BOM)
- `question_bank_sample.csv` (4 bank items, UTF-8-BOM)

### objective_grader.py changes
- `--make-samples` now uses `app.infrastructure.samples.sample_files.create_sample_files`
- demo fallback also uses new module
- No longer calls `legacy.create_sample_files`
