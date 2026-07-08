# Stage E2C Item-Analysis CSV Exporter

## 本次目标

实现 `ItemAnalysisCsvExporter`，生成与 legacy `write_item_analysis` 一致的 `item_analysis.csv`。不替换 workflow。

## 为什么第三步迁 item_analysis.csv

1. 13 个字段，每题一行 — 讲评课最常看的表
2. 复用 E2A 的 `csv_helpers.py`，零新基础设施
3. summary + detail + item_analysis = 教师讲评三件套

## 新增模块

```
app/infrastructure/exporters/item_analysis_csv_exporter.py
```

## legacy write_item_analysis 行为对照

| 行为 | legacy | 新 exporter |
|------|--------|------------|
| 字段顺序 | 13 字段 (见下) | 相同 |
| 编码 | UTF-8-BOM | 相同 |
| 空 rows | 写空文件 | 写表头 + warning |
| 数据来源 | answer_key + results 计算 | 预计算 rows |

## item_analysis.csv 字段顺序

```
question, question_id, question_status, difficulty, tags, answer, points,
accuracy, blank_rate, wrong_rate, partial_rate, invalid_rate, option_distribution
```

## 测试覆盖

| 测试 | 内容 |
|------|------|
| test_field_order_matches_legacy | 13 字段顺序 |
| test_round_trip_matches_legacy | 行数 + 首尾行 |
| test_encoding_utf8_bom | BOM + 字段名不污染 |
| test_empty_rows | 表头 + warning |
| test_exporter_does_not_import_legacy | AST 确认 |
| test_legacy_behavior_still_passes | 旧流程不受影响 |

## 本次未做内容

- 未迁移 item_stats 计算逻辑
- 未替换 app/workflow.py
- 未迁移 Excel / HTML / 其他 CSV

## 下一步建议

E2D: knowledge_profiles.csv exporter。
