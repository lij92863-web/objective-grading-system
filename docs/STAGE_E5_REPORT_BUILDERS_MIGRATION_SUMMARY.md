# Stage E5 Report Builders Migration Summary

## 已迁 builder 列表

| Builder | Legacy 函数 | 输出用途 | 字段数 |
|---------|-----------|---------|--------|
| build_simple_score_rows | simple_score_rows | 简单成绩表 (simple_score_report.xlsx 的数据源) | 13 |
| build_item_analysis_rows | item_stats | 每题分析 (item_analysis.csv 的数据源) | 10 |
| build_knowledge_profiles | build_knowledge_profiles | 知识点画像 (knowledge_profile.csv 的数据源) | 9 |
| build_class_report | build_class_report | 班级报告 (class_report.csv 的数据源) | 4 |
| build_validation_report | build_validation_report | 数据质量检查 (validation_report.csv 的数据源) | 4 |
| build_correct_question_ids | build_correct_question_ids | 已答对题目ID集合 | — |
| build_target_difficulties | build_target_difficulties | 目标难度映射 | — |
| build_practice_recommendations | recommend_practice | 练习推荐 (practice_recommendations.csv 的数据源) | 11 |

## 当前仍未替换 workflow 的原因

`app/workflow.py` 的 `run_grading()` 仍调用 legacy 的 build_* + write_* 函数。替换 workflow 需要：
1. 先让 report_builders + CSV exporters 的组合链路跑通
2. Excel/HTML 导出也迁到 exporters
3. 然后才能替换 workflow 中的调用

## 当前仍在 legacy 的内容

- Excel (write_workbook, write_simple_score_workbook)
- HTML (write_simple_report, write_advanced_dashboard, write_report_index)
- CSV helpers (write_dicts, read_csv_for_workbook)
- CLI 兼容入口

## 下一步建议

E3 Excel 迁移或 E6 workflow 替换。优先确保 report_builders + CSV exporters 的端到端链路可用。
