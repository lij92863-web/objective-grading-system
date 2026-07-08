# Stage E2B Detail CSV Exporter

## 本次目标

在 `app/infrastructure/exporters/` 下实现新的 detail CSV exporter，生成与 legacy `write_detail` 一致格式和编码的 `detail.csv`。不替换正式 workflow。

## 为什么第二步迁 detail.csv

1. 13 个字段，每个学生每题一行 — CSV 中最立体的一张表
2. 复用 E2A 的 `csv_helpers.py`，零新增基础设施
3. 迁完 summary + detail 后，两张最核心的 CSV 都被新 exporter 覆盖

## 新增模块

```
app/infrastructure/exporters/detail_csv_exporter.py    — DetailCsvExporter(ReportExporter)
```

## legacy write_detail 行为对照

| 行为 | legacy | 新 exporter |
|------|--------|------------|
| 字段顺序 | 13 字段 (见下) | 相同 |
| 编码 | UTF-8-BOM | 相同 |
| 空 rows | 写空文件 | 写表头 + warning |
| 数据来源 | answer_key + result.details | 预计算 rows |

## detail.csv 字段顺序

```
student_id, name, question, question_id, question_status, difficulty,
tags, expected, actual, raw_actual, score, max_score, status
```

## 新旧输出对比方式

1. 跑 legacy workflow 生成 `detail.csv`
2. 读取 legacy 输出 rows
3. 新 exporter 写 `detail.csv`
4. 对比表头、行数、首尾行内容、编码

## 测试覆盖

| 测试 | 内容 |
|------|------|
| test_field_order_matches_legacy | 13 字段顺序 |
| test_round_trip_matches_legacy | 行数 + 首尾行 + 关键字段 |
| test_encoding_is_utf8_bom | BOM + 字段名不污染 |
| test_empty_rows | 空 rows → 表头 + warning |
| test_exporter_does_not_import_legacy | AST 确认 |
| test_legacy_behavior_still_passes | 旧流程不受影响 |

## 本次未做内容

- 未替换 app/workflow.py
- 未删除 legacy
- 未迁移 Excel / HTML
- 未迁移其他 CSV

## 下一步建议

E2C: item_analysis.csv exporter — 复用 csv_helpers.py，新增 item_analysis_csv_exporter.py。
