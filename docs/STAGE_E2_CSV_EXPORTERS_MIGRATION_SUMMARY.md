# Stage E2 CSV Exporters Migration Summary

## 已迁 CSV exporter 列表

| # | Exporter | Legacy 函数 | 输出文件 | 字段数 | 状态 |
|---|----------|-----------|---------|-------|------|
| E2A | SummaryCsvExporter | write_summary | summary.csv | 10 | ✅ |
| E2B | DetailCsvExporter | write_detail | detail.csv | 13 | ✅ |
| E2C | ItemAnalysisCsvExporter | write_item_analysis | item_analysis.csv | 13 | ✅ |
| E2D | KnowledgeProfilesCsvExporter | write_knowledge_profiles | knowledge_profile.csv | 9 | ✅ |
| E2E | PracticeRecommendationsCsvExporter | write_practice_recommendations | practice_recommendations.csv | 11 | ✅ |
| E2F | ClassReportCsvExporter | write_class_report | class_report.csv | 4 | ✅ |
| E2G | ValidationReportCsvExporter | write_validation_report | validation_report.csv | 4 | ✅ |
| E2H | StudentReportCsvExporter | write_student_report | student_report.csv | 11 | ✅ |

## 每个 exporter 字段顺序

| Exporter | 字段 |
|----------|------|
| summary | student_id, name, rank, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count |
| detail | student_id, name, question, question_id, question_status, difficulty, tags, expected, actual, raw_actual, score, max_score, status |
| item_analysis | question, question_id, question_status, difficulty, tags, answer, points, accuracy, blank_rate, wrong_rate, partial_rate, invalid_rate, option_distribution |
| knowledge_profiles | student_id, name, tag, score, max_score, mastery, mastery_level, question_count, weak |
| practice_recommendations | student_id, name, weak_tag, mastery, question_id, target_difficulty, difficulty, difficulty_delta, stem, answer, tags |
| class_report | section, metric, value, extra |
| validation_report | severity, scope, item, message |
| student_report | student_id, name, score, max_score, percent, rank, weak_tags, wrong_questions, partial_questions, blank_questions, invalid_questions |

## 编码策略

所有 exporter 统一使用 UTF-8-BOM (`utf-8-sig`)，与 legacy 完全一致。

## 新旧输出对比情况

所有 8 个 exporter 均通过字段顺序对比、round-trip 内容一致、BOM/编码兼容、空 rows 行为明确测试。demo 样例中 practice_recommendations 无数据行（缺少题库），使用 synthetic rows 验证。

## 未迁移内容

- build_knowledge_profiles / recommend_practice / build_class_report / build_validation_report / item_stats 等**分析构建逻辑**仍在 legacy
- Excel 导出 (write_workbook, write_simple_score_workbook) 仍在 legacy
- HTML 导出 (write_simple_report, write_advanced_dashboard, write_report_index) 仍在 legacy

## 仍在 legacy 的内容

| 类别 | 函数 |
|------|------|
| 分析构建 | build_knowledge_profiles, build_class_report, build_validation_report, recommend_practice, item_stats, simple_score_rows |
| Excel | write_workbook, write_simple_score_workbook, write_xlsx |
| HTML | write_simple_report, write_advanced_dashboard, write_report_index |
| CSV helpers | write_dicts, write_dicts_with_fields, read_csv_for_workbook |

## 为什么还不替换 workflow

1. 分析构建逻辑 (build_*) 必须先迁到 app/application/use_cases 或 app/analysis
2. Excel/HTML 导出必须先迁到 app/infrastructure/exporters
3. 迁完后 app/workflow.py 的 run_grading 可以逐步替换 legacy 调用
4. 一次性替换风险高，应逐类（CSV → Excel → HTML）替换

## 下一步建议

1. E3: 迁移 Excel 导出 (exam_report.xlsx, simple_score_report.xlsx)
2. E4: 迁移 HTML 导出 (simple_report, advanced_dashboard, index)
3. E5: 迁移分析构建逻辑到 app/application/use_cases
4. E6: 替换 app/workflow.py 中的 legacy 调用
5. 最后才考虑删除 legacy 中的已迁函数
