# Stage E2A Summary CSV Exporter

## 本次目标

在 `app/infrastructure/exporters/` 下实现新的 CSV summary exporter，生成与 legacy `write_summary` 一致格式和编码的 `summary.csv`。不替换正式 workflow。

## 为什么先迁 summary.csv

1. 最简单 — 10 个字段，纯 CSV，无 Excel/HTML 复杂度
2. 最少依赖 — 只依赖 `write_dict_rows_csv` helper
3. 验证迁移模式 — 确认 `exporters/` 可以独立生成与 legacy 一致的输出

## 新增模块

```
app/infrastructure/exporters/
  csv_helpers.py              — write_dict_rows_csv()
  summary_csv_exporter.py     — SummaryCsvExporter(ReportExporter)
```

## legacy write_summary 行为对照

| 行为 | legacy | 新 exporter |
|------|--------|------------|
| 字段顺序 | student_id, name, rank, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count | 相同 |
| 编码 | UTF-8-BOM (utf-8-sig) | 相同 |
| 换行 | Python 默认 (newline="") | 相同 |
| 空 rows | 写空文件 (含 BOM) | 写表头文件 (含 BOM) + warning |
| 文件路径 | 由调用方指定 | ExportRequest.output_dir / summary.csv |

## 字段顺序

```
student_id, name, rank, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count
```

## 编码策略

- UTF-8 with BOM (`utf-8-sig`)
- 与 legacy 完全一致
- Python `csv.DictReader` 正常读取，BOM 不污染字段名

## 新 exporter 入口

```python
from app.infrastructure.exporters.summary_csv_exporter import SummaryCsvExporter
from app.infrastructure.exporters.contracts import ExportRequest

exporter = SummaryCsvExporter()
result = exporter.export(ExportRequest(output_dir=Path("./out")), rows)
```

## 新旧输出对比方式

1. 先跑 legacy workflow 生成 `summary.csv`
2. 读取 legacy 输出的 rows
3. 用新 exporter 写 `summary.csv`
4. 对比表头、行数、第一行内容、编码 (BOM)

## 测试覆盖

| 测试 | 覆盖内容 |
|------|---------|
| test_field_order_matches_legacy | 10 字段顺序与 legacy 一致 |
| test_round_trip_matches_legacy | 行数、第一行内容一致 |
| test_encoding_is_utf8_bom | BOM 存在且不污染字段名 |
| test_empty_rows_writes_header_only | 空 rows → 表头文件 + warning |
| test_exporter_does_not_import_legacy | AST 扫描确认无 legacy import |
| test_legacy_exporter_behavior_still_passes | 旧测试仍通过 |

## 本次未做内容

- 没有替换 app/workflow.py
- 没有删除 legacy
- 没有迁移 Excel (exam_report.xlsx)
- 没有迁移 HTML (simple_report.html / advanced_dashboard.html)
- 没有迁移其他 CSV (detail / item_analysis / knowledge_profiles)

## 下一步建议

E2B: detail.csv exporter — 复用 `csv_helpers.py`，新增 `detail_csv_exporter.py`。
逐张 CSV 迁移，迁一张锁一张测试。

---

**关联文档**：
- `docs/EXPORTER_MIGRATION_AUDIT.md` — 审计文档
- `app/infrastructure/exporters/contracts.py` — 接口定义
- `tests/test_exporter_legacy_behavior.py` — 旧行为回归测试
