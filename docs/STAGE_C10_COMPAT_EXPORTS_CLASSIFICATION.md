# Stage C10 — COMPAT_EXPORTS Classification

## Total: 125 symbols (reduced from 146 in original, some duplicates removed)

### Category A: New implementation exists, kept for compatibility
load_answer_key, load_submissions, load_question_bank, grade_all, grade_submission, score_answer, score_answer_detail, write_summary, write_detail, write_item_analysis, write_knowledge_profiles, write_practice_recommendations, write_class_report, write_student_report, write_validation_report, write_workbook, write_simple_score_workbook, write_xlsx, write_simple_report, write_advanced_dashboard, write_report_index, item_stats, simple_score_rows, basic_stats, build_knowledge_profiles, build_validation_report, build_class_report, build_correct_question_ids, build_target_difficulties, recommend_practice, create_sample_files, html_escape, safe_slug

### Category B: Not yet migrated
ExamMeta, BankQuestion, KnowledgeProfile, StudentResult, Submission, QuestionSpec, QuestionResult, AnswerKey, competition_ranks, mastery_level, read_csv_for_workbook, build_parser, main, print_console_report, build_abnormal_items, build_question_accuracy_items, build_score_distribution, build_teaching_suggestions, build_weak_items, build_weak_tags, main_wrong_answer, get_rate_class, render_*, report_css, advanced_dashboard_css, score_bands, student_status_map, format_answer, format_expected_answer, normalize_answer, is_choice_answer, is_choice_like_answer, matches_text_answer, allowed_options, pct, percent, split_tags, split_aliases, first_present, parse_bool, parse_difficulty, parse_optional_float, parse_question_number, parse_status, numeric_value, difficulty_rank, read_csv, write_dicts, write_dicts_with_fields, worksheet_xml, xml_attr, excel_column_name, escape, bar, report_link, archive_reports

### Category C: Facade files depend on
All symbols in COMPAT_EXPORTS — facades now import via app/compat ✅

### Category D: Tests baseline only
Most symbols — 30+ test files import legacy for baseline comparison

### Category E: Internal helpers, future deletion candidates
escape, excel_column_name, worksheet_xml, xml_attr, difficulty_rank, bar, report_link, OPTION_RE, QUESTION_RE, TRUTHY, EPSILON, FIELD_ALIASES, QUESTION_STATUSES, CHOICE_OPTIONS

## Category F: Public API, must keep
grade_all, load_answer_key, load_submissions, write_summary, write_workbook, write_simple_report, item_stats, simple_score_rows, create_sample_files — these are the most likely to be imported by external scripts
