# Stage L7A Legacy Dependency Scan

Date: 2026-07-09

## Baseline

- Branch: `main`
- Starting commit: `1611fa6 docs record report archiver status`
- Starting `git status --short`: clean
- `python run_tests.py`: 553 passed, 5 skipped
- `python -m unittest discover -s tests -p "test*.py"`: passed

The unittest discovery run still prints existing `ResourceWarning` messages from
`tests/test_csv_report_pipeline_shadow_parity.py`, but the suite result is OK.

## Workflow Legacy Import

`app/workflow.py` still imports `legacy.objective_grader_legacy as legacy`.

Current legacy calls and references:

- `legacy.safe_slug`
- type hints for `StudentResult`, `KnowledgeProfile`, `BankQuestion`, `ExamMeta`
- `legacy.html_escape`
- `legacy.load_answer_key`
- `legacy.load_submissions`
- `legacy.grade_all`
- `legacy.ExamMeta`
- `legacy.build_knowledge_profiles`
- `legacy.load_question_bank`
- `legacy.build_validation_report`
- `legacy.basic_stats`
- `legacy.write_validation_report`

Already removed before this stage:

- `legacy.simple_score_rows`
- `legacy.item_stats`
- legacy CSV write helpers
- legacy Excel write helpers
- legacy HTML write helpers

## CLI Legacy Import

`objective_grader.py` still imports legacy in two ways:

- `from legacy.objective_grader_legacy import *` for compatibility exports.
- `from legacy import objective_grader_legacy as legacy` for
  `legacy.create_sample_files` in `--make-samples` and no-input demo mode.

`objective_grader.py` does not directly call legacy loaders or report writers.
The loader calls are currently inside `app/workflow.py`.

## Ready To Migrate In This Round

Ready candidates:

- `legacy.load_answer_key`
- `legacy.load_submissions`
- `legacy.write_validation_report`
- `legacy.build_knowledge_profiles`, if existing application builder parity is
  sufficient for workflow use.
- `legacy.build_validation_report`, if existing application builder parity is
  sufficient for workflow use.
- `legacy.basic_stats`, with a small application builder if needed.

Needs audit before cutover:

- `legacy.grade_all`, because grading output shape and scoring rules are
  high-risk and must match exactly.
- `objective_grader.py` compatibility star import, because tests and external
  callers may depend on it.
- `legacy.create_sample_files`, because replacing it requires preserving demo
  and `--make-samples` output behavior.

## Tests As Baseline

Legacy imports in tests remain allowed as behavioral baselines. Migration tests
use legacy to prove new infrastructure/application/domain code preserves output
shape and behavior.

## Out Of Scope For This Round

- Modifying or deleting `legacy/**`
- Changing CLI arguments
- Changing CSV, Excel, or HTML report format
- Changing web UI
- Connecting real APIs or reading `.env`
