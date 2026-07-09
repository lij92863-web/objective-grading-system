# Stage E3C — WorkbookExporter

## 目标

将 `exam_report.xlsx`（9 sheets）从 legacy 迁到 `app/infrastructure/exporters/`。

## 文件

- `app/infrastructure/exporters/workbook_exporter.py`
- `tests/test_workbook_exporter.py`

## 类：WorkbookExporter

### 输入

`List[Tuple[str, Path]]` — 有序列表，每项为 (sheet_name, csv_path)。

9 个 sheet（顺序固定，与 legacy 完全一致）：

| # | Sheet 名 | CSV 来源 |
|---|---------|---------|
| 1 | 成绩总表 | summary.csv |
| 2 | 每题明细 | detail.csv |
| 3 | 每题分析 | item_analysis.csv |
| 4 | 知识点画像 | knowledge_profile.csv |
| 5 | 学生错题 | student_wrong_list.csv |
| 6 | 讲评计划 | teaching_plan.csv |
| 7 | 班级补救 | class_remedial_package.csv |
| 8 | 分层补救 | layered_remedial_plan.csv |
| 9 | 数据质量检查 | validation_report.csv |

### 输出

`exam_report.xlsx`，9 个 sheet，inlineStr 单元格。

### 技术路线

使用 `xlsx_helpers.py`（标准库 zipfile + inlineStr）。CSV 读取使用 `csv.reader`（标准库）。

### 返回

`ExportResult(status="ok", generated_files=["exam_report.xlsx"])`

## 与 legacy 一致性

| 维度 | legacy | new |
|------|--------|-----|
| 文件名 | exam_report.xlsx | ✅ |
| Sheet 数量 | 9 | ✅ |
| Sheet 名 | 9 个中文名 | ✅ |
| Sheet 顺序 | 固定顺序 | ✅ |
| 单元格方式 | inlineStr | ✅ |
| 样式 | 无（无 openpyxl 时） | ✅ |
| 中文编码 | UTF-8 | ✅ |

## 测试覆盖

| 测试 | 内容 |
|------|------|
| test_exporter_writes_valid_xlsx | 文件存在、>1KB、ZIP 合法 |
| test_sheet_names_and_order_match_legacy | 9 sheet 名和顺序 |
| test_sheet_count_matches_legacy | sheet 数量 = 9 |
| test_headers_match_for_key_sheets | 核心 sheet 表头 |
| test_first_data_rows_match_for_key_sheets | 核心 sheet 首行数据 |
| test_chinese_not_garbled | 中文不乱码 |
| test_no_legacy_import | AST 审计不含 legacy |
| test_no_web_import | AST 审计不含 web |
| test_no_openpyxl_import | AST 审计不含 openpyxl |
| test_old_workflow_still_unaffected | 旧 workflow 不受影响 |
