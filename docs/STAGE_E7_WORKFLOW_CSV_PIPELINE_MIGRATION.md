# Stage E7 Workflow CSV Pipeline Migration

## 目标

把 `app/workflow.py` 的 CSV 输出从 legacy 切到新 `csv_report_pipeline`。

## E6 Shadow 对比结论

8 个 CSV 与 legacy 输出完全一致（字段顺序、行数、内容、编码）。E6B shadow parity 测试通过。

## Workflow 修改点

`app/workflow.py:run_grading()` 中第 468-485 行（8 个 legacy CSV write_* 调用）替换为一个 `run_csv_report_pipeline()` 调用。

## 哪些 CSV 已切到新 pipeline

| CSV | 旧调用 | 新调用 |
|-----|--------|--------|
| summary.csv | legacy.write_summary | SummaryCsvExporter |
| detail.csv | legacy.write_detail | DetailCsvExporter |
| item_analysis.csv | legacy.write_item_analysis | ItemAnalysisCsvExporter |
| knowledge_profile.csv | legacy.write_knowledge_profiles | KnowledgeProfilesCsvExporter |
| practice_recommendations.csv | legacy.write_practice_recommendations | PracticeRecommendationsCsvExporter |
| class_report.csv | legacy.write_class_report | ClassReportCsvExporter |
| validation_report.csv | legacy.write_validation_report (error path still legacy) | ValidationReportCsvExporter |
| student_report.csv | legacy.write_student_report | StudentReportCsvExporter |

## 哪些 legacy 调用仍保留

- `legacy.write_validation_report` — 阻塞错误路径（非主 CSV 流）
- `legacy.write_workbook` + `write_simple_score_workbook` — Excel
- `legacy.write_simple_report` + `write_advanced_dashboard` + `write_report_index` — HTML
- `legacy.simple_score_rows` + `legacy.item_stats` — 供 Excel/HTML 使用的 rows

## 为什么 Excel / HTML 仍保留 legacy

1. Excel 导出 (write_workbook) 需要 `openpyxl`，迁移需单独处理
2. HTML dashboard (write_advanced_dashboard) 内部逻辑复杂，包含大量 CSS/图表渲染
3. 逐类迁移风险更低：CSV 先切，Excel 次之，HTML 最后

## 旧 CLI smoke 结果

`objective_grader.py` 用 demo 样例批改成功，8 CSV + Excel + HTML 均正常输出。

## 测试覆盖

| 测试 | 覆盖 |
|------|------|
| test_workflow_csv_pipeline_integration | 8 CSV + Excel/HTML 存在，CLI 可用 |
| test_workflow_legacy_csv_call_guard | workflow 不含 legacy CSV write_* 调用 |
| test_csv_report_pipeline_shadow_parity | 8 CSV 新旧对比 |

## 当前风险

- `legacy.write_validation_report` 仍在错误路径 — 后续可迁
- Excel/HTML 仍在 legacy — 独立任务
- 如果后续有人在 workflow 中重新 import legacy CSV write_*，guard 测试会拦截

## 下一阶段建议

E3: Excel 导出迁移
