# Recognition Safety Regression Matrix V5

| Risk | Expected behavior | Test file | Fixture | Status | Remaining caveat |
| --- | --- | --- | --- | --- | --- |
| fixture not used | loader reads all batch fixtures | `tests/test_synthetic_batch_loader.py` | all 8 | pass | synthetic only |
| expected copied as actual | evaluator compares actual to expected | `tests/test_fixture_driven_batch_orchestrator_v4.py` | all 8 | pass | no real paper |
| qwen budget simulated | policy orchestrator decides budget | `tests/test_qwen_budget_truth.py` | qwen_budget_exceeded | pass | fake Qwen only |
| blocked_by_budget not counted | counter is returned in summary | `tests/test_qwen_policy_orchestrator_counters.py` | qwen_budget_exceeded | pass | no API |
| teacher summary hardcoded | summary uses `from_models` | `tests/test_teacher_summary_from_models.py` | qwen_budget_exceeded | pass | synthetic model |
| identity substring guard | exact registry is required | `tests/test_no_substring_identity_guard.py` | identity fixtures | pass | app/recognition scan |
| global exception missing | review queue includes exact codes | `tests/test_error_code_exact_sets.py` | all risks | pass | synthetic only |
| invalid option auto fixed | invalid option remains blocking | `tests/test_synthetic_batch_fixtures_v4.py` | invalid_option | pass | no formal grading |
| missing roi ignored | missing ROI remains blocking | `tests/test_synthetic_batch_fixtures_v4.py` | missing_roi | pass | no real image |
| formal report generated | recognition scripts do not generate reports | existing guard tests | none | pass | report pipeline untouched |
| direct grade_all | recognition remains isolated | existing safe bridge guard | none | pass | bridge dry-run only |
| real API call | default Qwen path fail-closed | `tests/test_qwen_real_client_safety.py` | none | pass | explicit flag still required |
| secret leak | sanitizer and guard tests scan output | existing guard tests | none | pass | no raw response |
| base64 output | snapshot and scripts avoid base64 | existing guard tests | none | pass | fixtures only |
| real class use | readiness and small batch gates false | `tests/test_real_paper_readiness_gate_v2.py` | none | pass | not allowed |
