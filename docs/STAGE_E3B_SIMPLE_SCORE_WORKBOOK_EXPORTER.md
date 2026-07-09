# Stage E3B2 — SimpleScoreWorkbookExporter

## 目标

将 `simple_score_report.xlsx` 从 legacy 迁到 `app/infrastructure/exporters/`。

## 文件

- `app/infrastructure/exporters/simple_score_workbook_exporter.py`
- `tests/test_simple_score_workbook_exporter.py`

## 类：SimpleScoreWorkbookExporter

### 输入

`List[Dict[str, Any]]` — 由 `legacy.simple_score_rows(results)` 生成的 dict list。

13 个字段（顺序固定）：rank, student_id, name, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count, wrong_questions, blank_questions, remark

### 输出

`simple_score_report.xlsx`，1 个 sheet：`scores`。

### 技术路线

使用 `xlsx_helpers.py`（标准库 zipfile + inlineStr），不 import legacy/web/openpyxl/xlsxwriter/pandas。

### 返回

`ExportResult(status="ok", generated_files=["simple_score_report.xlsx"])`

## 与 legacy 一致性

| 维度 | legacy | new |
|------|--------|-----|
| 文件名 | simple_score_report.xlsx | ✅ 一致 |
| Sheet 名 | scores | ✅ 一致 |
| 字段顺序 | 13 字段固定 | ✅ 一致 |
| 单元格方式 | inlineStr | ✅ 一致 |
| 中文编码 | UTF-8 | ✅ 一致 |

## 测试覆盖

| 测试 | 内容 |
|------|------|
| test_exporter_writes_valid_xlsx | 文件存在、>1KB、ZIP 合法 |
| test_sheet_name_matches_legacy | sheet 名与 legacy 一致 |
| test_header_matches_legacy | 表头与 legacy 一致 |
| test_row_count_matches_legacy | 行数与 legacy 一致 |
| test_first_data_row_matches_legacy | 首行数据一致 |
| test_chinese_not_garbled | 中文不乱码 |
| test_no_legacy_import | AST 审计不含 legacy |
| test_no_web_import | AST 审计不含 web |
| test_no_openpyxl_import | AST 审计不含 openpyxl |
| test_generated_files_in_result | ExportResult 包含 xlsx |
| test_old_workflow_still_unaffected | 旧 workflow 不受影响 |
