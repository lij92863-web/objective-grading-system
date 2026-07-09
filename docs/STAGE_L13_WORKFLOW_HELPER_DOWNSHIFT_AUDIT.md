# Stage L13 — Workflow Helper Downshift Audit

> Date: 2026-07-09

## workflow.py Local Helpers

| # | Helper | Type | Uses legacy? | Safe to migrate? | Target |
|---|--------|------|-------------|------------------|--------|
| 1 | `safe_slug` | shared/string | yes (calls legacy) | ✅ | use `html_helpers.safe_slug` |
| 2 | `html_escape` (via legacy.*) | shared/string | yes (calls legacy) | ✅ | use `html_helpers.html_escape` |
| 3 | `write_json` | infrastructure | no | ✅ | `app/infrastructure/reports/` |
| 4 | `write_dicts` | infrastructure | no | ✅ | `app/infrastructure/reports/` |
| 5 | `read_csv_dicts` | infrastructure | no | ✅ | `app/infrastructure/reports/` |
| 6 | `display_percent` | shared/format | no | ✅ | `app/shared/` |
| 7 | `main_wrong_answer_from_distribution` | application | no | ✅ | `app/application/use_cases/` |
| 8 | `teaching_level` | application | no | ✅ | `app/application/use_cases/` |
| 9 | `build_teaching_plan` | application | no | ✅ | `app/application/use_cases/` |
| 10 | `build_student_wrong_list` | application | yes (type hints) | ⚠️ type dep | defer |
| 11 | `build_class_remedial_package` | application | yes (type hints) | ⚠️ type dep | defer |
| 12 | `build_layered_remedial_plan` | application | yes (type hints) | ⚠️ type dep | defer |
| 13 | `write_teacher_html` | infrastructure | yes (html_escape) | ✅ (after #2) | `app/infrastructure/reports/` |
| 14 | `write_error_report` | infrastructure | no | ✅ | `app/infrastructure/reports/` |
| 15 | `append_teaching_priority_to_dashboard` | infrastructure | yes (html_escape) | ✅ (after #2) | `app/infrastructure/reports/` |
| 16 | `replace_report_outputs` | infrastructure | no | ✅ | `app/infrastructure/reports/` |
| 17 | `archive_exam_reports` | infrastructure | yes (ExamMeta) | ⚠️ type dep | defer |
| 18 | `profile_row_to_object` | adapter | no | ✅ | `app/application/` |
| 19 | `answer_key_to_validation_dict` | adapter | no | ✅ | `app/application/` |

## Round 1 (L13B): Safe to do now

Switch `legacy.safe_slug` → `html_helpers.safe_slug` and `legacy.html_escape` → `html_helpers.html_escape` in workflow.py.

## Round 2 (L13C): Type-dep free helpers

`display_percent`, `main_wrong_answer_from_distribution`, `teaching_level`, `build_teaching_plan`, `write_teacher_html`, `append_teaching_priority_to_dashboard`, `write_error_report`, `replace_report_outputs`, `write_json`, `write_dicts`, `read_csv_dicts`, `profile_row_to_object`, `answer_key_to_validation_dict`

These can migrate to:
- `app/shared/` — string/format helpers
- `app/application/use_cases/` — business logic helpers  
- `app/infrastructure/reports/` — file I/O helpers

## Deferred

`build_student_wrong_list`, `build_class_remedial_package`, `build_layered_remedial_plan`, `archive_exam_reports` — depend on legacy types (StudentResult, KnowledgeProfile, BankQuestion, ExamMeta). Defer until types are decoupled from legacy.
