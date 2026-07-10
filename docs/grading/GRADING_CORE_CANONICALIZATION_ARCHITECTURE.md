# Grading Core Canonicalization Architecture

```text
Input Loader
  -> Canonical Domain Models
  -> Grading Precheck
       -> BLOCKED: validation/error artifacts only
       -> ALLOWED: deterministic grade_all
          -> post-grade consistency validation
          -> report pipelines
```

`app/domain/grading/models.py` is the only entity source. `normalize.py` is the only grading normalization source. `QuestionType` is the strict type vocabulary. `PrecheckReport` alone decides whether scoring may start; renderers only display it. Infrastructure imports domain objects and never defines them.

The typed application boundary is `GradingRunRequest -> GradingRunResult`. `workflow.run_grading` remains a compatibility wrapper. Structured `GradingOverride` is audited and cannot waive missing/conflicting keys, unknown types/statuses, duplicate identity conflict, unconfirmed drafts or invalid domain objects.

Dependencies flow application -> infrastructure/domain and infrastructure -> domain. Domain must not import infrastructure, workflow, web or reports. Failure is closed before scoring. Reports and archives are downstream only. Future report-pipeline consolidation is explicitly out of scope.
