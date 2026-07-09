# Stage L17 — Main-Chain No-Legacy Gate

## Definition of "main chain"

- `app/domain/**` — grading core
- `app/application/**` — use cases / business logic
- `app/infrastructure/**` — file I/O, exporters, loaders
- `app/shared/**` — string/format utilities
- `app/workflow.py` (normal grading path)
- `objective_grader.py` (ordinary CLI grading path)

## Gate status: PASS

- domain: no legacy imports ✅
- application: no legacy imports ✅
- infrastructure: no legacy imports ✅
- shared: no legacy imports ✅
- workflow (normal path): no legacy calls for grading/loading/exporting ✅
- objective_grader (ordinary path): no legacy calls for grading/loading/exporting ✅

## Known exceptions (allowed)

| File | Allowed import | Reason |
|------|---------------|--------|
| `app/workflow.py` | `from legacy import ...` | ExamMeta, load_question_bank only |
| `app/validators.py` | legacy import | Facade, error-path only |
| `objective_grader.py` | legacy import | COMPAT_EXPORTS only |
| `app/analysis.py` | legacy import | Facade |
| `app/reports.py` | legacy import | Facade |
| `app/core.py` | legacy import | Facade |
| `tests/**` | legacy import | Baseline tests |
