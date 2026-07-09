# Recognition Safety Regression Matrix v4

| Risk | Expected | Test File | Status |
|------|----------|-----------|--------|
| block_submission | ready=False | test_review_resolution_p0_regression | pass |
| item_id mismatch | fail closed | test_review_resolution_p0_regression | pass |
| empty candidate accept | fail closed | test_review_resolution_p0_regression | pass |
| identity conflict | ready=False | test_review_resolution_p0_regression | pass |
| identity missing | ready=False | test_review_queue_acceptance | pass |
| unresolved pending | ready=False | test_review_resolution_p0_regression | pass |
| unresolved blocking | ready=False | test_review_resolution_p0_regression | pass |
| rejected candidate | not in final | test_review_resolution_p0_regression | pass |
| invalid option | blocking | test_review_queue_acceptance | pass |
| missing roi | blocking | batch_orchestrator | pass |
| qwen disabled | needs_review | test_qwen_guard_acceptance | pass |
| qwen budget exceeded | needs_review | batch_orchestrator | pass |
| malformed response | engine_error | test_omr_qwen_fusion | pass |
| omr qwen conflict | needs_review | test_omr_qwen_fusion | pass |
| teacher summary safety | no secrets | test_teacher_facing_summary | pass |
| formal report guard | no report | test_no_formal_report | pass |
| no grade_all guard | no import | test_recognition_forbidden_file_guard | pass |
| no real api guard | fail-closed | test_qwen_guard_acceptance | pass |