# Stage L10 Grading Core Entry Audit

## L10A Audit

`app/workflow.py` still calls:

- `legacy.grade_all(answer_key, submissions)`

Legacy input:

- `AnswerKey` with `questions`, `duplicate_questions`, `total_points`, and
  `by_number`.
- Iterable of `Submission`.

Legacy output:

- List of `StudentResult`.
- Each result contains score totals, status counts, and per-question details.

Domain equivalent:

- `app.domain.grading.scoring.grade_all`
- Re-exported by `app.domain.grading`.
- It accepts the same answer key and submission shape used by the migrated CSV
  loaders.
- It returns domain `StudentResult` objects with fields expected by workflow and
  report builders.

Existing coverage:

- `tests/test_grading_core.py`
- `tests/test_enhanced_grading.py`
- choice, blank, and true/false scoring tests.

L10A baseline added:

- `tests/test_grading_core_entry_baseline.py` compares legacy `grade_all` and
  domain `grade_all` on demo answer key/submission data.
- The comparison covers top-level score fields and per-question detail fields
  used by downstream reports.
- The test also verifies the domain grading modules do not import legacy.

L10A conclusion: domain `grade_all` is an equivalent workflow entry candidate.
The remaining risk is accidental output-shape drift in downstream reports, so
L10B must include workflow guard and full report smoke tests.
