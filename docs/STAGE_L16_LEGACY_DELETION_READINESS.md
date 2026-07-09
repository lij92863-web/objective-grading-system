# Stage L16 — Legacy Deletion Readiness

## Current legacy importers

| File | Imports legacy? | Reason |
|------|----------------|--------|
| `app/workflow.py` | YES | ExamMeta, load_question_bank (whitelist) |
| `app/validators.py` | YES | Facade — uses build_validation_report |
| `app/analysis.py` | YES | Facade — re-exports legacy functions |
| `app/reports.py` | YES | Facade — re-exports legacy functions |
| `app/core.py` | YES | Facade — re-exports legacy functions |
| `objective_grader.py` | YES | COMPAT_EXPORTS compatibility |
| `app/domain/**` | NO | ✅ |
| `app/application/**` | NO | ✅ |
| `app/infrastructure/**` | NO | ✅ |
| `tests/**` | YES (many) | Baseline tests — expected and allowed |

## Deletion Candidate Matrix

### A. Can delete (future, not this round)
- CSV writers (write_summary, write_detail, etc.) — migrated to exporters
- Excel writers (write_workbook, write_xlsx, etc.) — migrated to exporters
- HTML writers (write_simple_report, etc.) — migrated to exporters
- load_answer_key, load_submissions — migrated to infrastructure/loaders
- grade_all — migrated to domain/grading
- build_knowledge_profiles, build_validation_report, basic_stats — migrated
- simple_score_rows, item_stats — migrated
- create_sample_files — migrated to infrastructure/samples

### B. Cannot delete yet
- ExamMeta dataclass — still used by workflow for archive
- load_question_bank — still used by workflow
- Functions needed by COMPAT_EXPORTS in objective_grader.py
- Functions used by app/validators.py for error path

### C. Move to compat layer (future)
- All symbols in COMPAT_EXPORTS

### D. Need next round
- workflow ExamMeta dependency
- workflow load_question_bank dependency
- app/validators.py build_validation_report dependency

## Deletion prerequisites
1. workflow uses domain ExamMeta (not legacy)
2. workflow uses infrastructure load_question_bank
3. app/validators.py uses new validation builder
4. COMPAT_EXPORTS narrowed or moved to compat module
5. All legacy-dependent tests updated or flagged

## Why NOT deleting now
Legacy is still the single source of truth for dataclass definitions and compatibility API. Premature deletion would break tests and scripts.
