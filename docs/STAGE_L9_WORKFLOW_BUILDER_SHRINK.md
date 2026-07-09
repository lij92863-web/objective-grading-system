# Stage L9 Workflow Builder Shrink

## L9A Audit

`app/workflow.py` still calls three legacy builder-style functions:

- `legacy.build_knowledge_profiles(answer_key, results, weak_threshold=...)`
- `legacy.build_validation_report(answer_key, submissions, results, profiles,
  question_bank)`
- `legacy.basic_stats(results)`

No remaining workflow calls were found for:

- `legacy.build_class_report`
- `legacy.build_practice_recommendations`
- `legacy.build_student_report`
- `legacy.build_item_analysis`
- `legacy.build_score_rows`

Existing application equivalents:

- `app.application.use_cases.report_builders.knowledge_profiles` provides
  `build_knowledge_profiles`.
- `app.application.use_cases.report_builders.validation_report` provides
  `build_validation_report`.
- Both modules already have legacy parity tests and no-legacy import guards.

Missing application equivalent:

- `legacy.basic_stats` does not yet have an application-layer replacement.

Shape mismatch to handle before cutover:

- Workflow currently holds legacy/domain objects such as `AnswerKey`,
  `Submission`, `StudentResult`, and `KnowledgeProfile`.
- Existing application builders accept dictionary-shaped inputs and return
  dictionary-shaped rows.
- Workflow's success path and validation/error path still need the same
  downstream object shapes as before.

Recommended L9B path:

- Add a small `basic_stats` application builder that matches
  `legacy.basic_stats`.
- Route workflow to the existing application builders using local conversion
  helpers scoped to workflow orchestration, or enhance the builders to accept
  the object shapes without importing legacy.
- Keep `profiles` compatible with downstream workflow/exporter code.
- Add workflow guard tests to prevent calls to the three migrated legacy
  builders.

Risk:

- `build_validation_report` must see the same `profiles` fields after the
  knowledge-profile cutover.
- `profiles` are also passed into the CSV pipeline, HTML exporters, and workbook
  exporter; changing their shape would change report behavior.

L9A conclusion: `build_knowledge_profiles`, `build_validation_report`, and
`basic_stats` are candidates for L9B migration, but the cutover must preserve
downstream profile object compatibility.
