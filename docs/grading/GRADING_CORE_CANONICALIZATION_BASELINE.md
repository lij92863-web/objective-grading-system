# Grading Core Canonicalization Baseline

- Start commit: `c5de1f6b4225caf8e986c1dd21a426f3d669a209`.
- Baseline: `run_tests.py` 1550 passed / 5 skipped; default discover 1537 passed / 5 skipped plus a separate 19-test output.
- Canonical-looking domain definitions currently live in `app/domain/grading/models.py`, but `app/infrastructure/loaders/csv_loaders.py` independently defines QuestionSpec, AnswerKey and Submission.
- `normalize_answer` is duplicated in domain normalize and CSV loader.
- `run_grading_precheck` exists in domain precheck but `workflow.run_grading` loads then calls `grade_all` before validation.
- Loader output currently uses loader-private dataclasses and does not populate `question_type`.
- Compatibility entry points include `workflow.run_grading`, CSV loaders, application CSV report adapters and existing CLI tests.
- `allow_errors=True` currently bypasses all renderer-derived blocking validation.
