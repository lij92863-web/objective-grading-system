# Stage L7 CSV Loaders Migration

Date: 2026-07-09

## L7B Legacy Behavior Audit

Audited legacy functions:

- `load_answer_key(path)`
- `load_submissions(path, answer_key)`

Input paths used for demo audit:

- `samples/demo_exam/answer_key_sample.csv`
- `samples/demo_exam/submissions_sample.csv`

## Legacy Reader Behavior

The legacy loader uses the standard library `csv.DictReader` through a shared
`read_csv(path)` helper.

Encoding:

- Files are opened with `encoding="utf-8-sig"` and `newline=""`.
- Chinese text is preserved in answer-key tags and submission names.

Missing files:

- Missing paths raise `FileNotFoundError` from `Path.open`.

Missing header:

- Empty CSVs or files without field names raise `ValueError`.

Missing answer-key question number:

- A row without a recognized question field raises `ValueError` with row
  context.

Answer key output structure:

- Returns an `AnswerKey` object with `questions`, `duplicate_questions`,
  `total_points`, and `by_number`.
- Each question has `number`, `answers`, `points`, `partial_credit`,
  `partial_points`, `tags`, `source_id`, `difficulty`, `answer_text`,
  `answer_aliases`, `tolerance`, and `status`.
- Duplicate question numbers are recorded in `duplicate_questions` and skipped
  after the first occurrence.

Submission output structure:

- Returns a list of `Submission` objects.
- Each submission has `student_id`, `name`, `answers`, `raw_answers`,
  `extra_questions`, and `row_number`.
- Question columns are detected from headers such as `Q1`.
- Blank cells normalize to an empty `frozenset()` and retain an empty raw value.
- Extra question columns are recorded in `extra_questions`.

Workflow dependency:

- `app/workflow.py` currently calls `legacy.load_answer_key` and
  `legacy.load_submissions`.

CLI dependency:

- `objective_grader.py` does not call loaders directly; it calls
  `run_grading`, where workflow currently loads CSVs.

Migration decision:

- The loader behavior is small enough to migrate into
  `app.infrastructure.loaders.csv_loaders` without importing legacy.
- New loader dataclasses must preserve the legacy attribute surface and
  computed properties used by workflow and existing grading/report builders.

## L7C Migration Result

Implemented `app.infrastructure.loaders.csv_loaders` with no legacy or web
imports. The new loader uses stdlib `csv.DictReader`, `utf-8-sig`, and local
dataclasses that preserve the legacy attribute surface:

- `QuestionSpec`
- `AnswerKey`
- `Submission`

Parity tests compare demo answer keys, demo submissions, Chinese fields, blank
cells, missing files, and missing question fields against the legacy baseline.

## L7D Workflow Cutover Result

`app/workflow.py` now imports `load_answer_key` and `load_submissions` from
`app.infrastructure.loaders.csv_loaders`.

Cutover notes:

- `workflow.py` no longer calls `legacy.load_answer_key`.
- `workflow.py` no longer calls `legacy.load_submissions`.
- `objective_grader.py` was not changed in L7D because it does not call loaders
  directly. It delegates to `run_grading`.
- CLI arguments and output filenames are unchanged.
