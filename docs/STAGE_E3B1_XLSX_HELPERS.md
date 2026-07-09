# Stage E3B1 — Standard Library XLSX Helpers

## 目标

提供最小、稳定、可测试的纯 Python 标准库 XLSX 写入工具，供后续 E3B2-E3C exporter 使用。

## 技术路线

Route B（标准库 zipfile + xml），遵循 E3A-H 审计结论。

## 文件

- `app/infrastructure/exporters/xlsx_helpers.py` — 实现
- `tests/test_xlsx_helpers.py` — 测试
- `docs/STAGE_E3B1_XLSX_HELPERS.md` — 本文档

## 依赖

**仅标准库**：`zipfile`, `xml.sax.saxutils`, `pathlib`, `dataclasses`, `datetime`, `typing`

不依赖 openpyxl、xlsxwriter、pandas 或任何第三方库。

## API

### `XlsxSheet`

```python
@dataclass
class XlsxSheet:
    name: str                         # sheet 名称（>31 字符自动截断）
    rows: List[List[Any]]             # 行数据
```

### `write_xlsx(path, sheets) -> Path`

```python
write_xlsx(
    Path("out.xlsx"),
    [XlsxSheet(name="成绩", rows=[["姓名", "分数"], ["张三", "95"]])],
)
```

返回写入的 Path（方便链式调用）。

## 输出特征

| 特性 | 值 |
|------|-----|
| 压缩 | ZIP_DEFLATED |
| 单元格类型 | inlineStr（不使用 sharedStrings） |
| 样式 | 无（不生成 styles.xml） |
| 公式 | 不支持 |
| 列宽 | 无 |
| 冻结窗格 | 无 |
| OOXML 文件 | [Content_Types].xml, _rels/.rels, xl/workbook.xml, xl/_rels/workbook.xml.rels, xl/worksheets/sheetN.xml |
| 多 sheet | 支持 |
| 中文 | 完整支持 |
| XML escape | 处理 `<`, `>`, `&`, `"` |
| 空 sheet | 自动填充 `["empty"]` 行 |

## 与 legacy 一致性

本 helper 的 XLSX 结构与 `legacy.write_xlsx()` 完全一致：
- 相同的 OOXML 文件清单
- 相同的 inlineStr 策略
- 相同的 ZIP_DEFLATED 压缩
- 相同的 sheet 名截断逻辑（31 字符）

## 与 legacy 的区别

- 使用 `XlsxSheet` dataclass 替代 `Tuple[str, List[List[str]]]`
- 放在 `app/infrastructure/exporters/` 而非 `legacy/`
- 不 import legacy

## 测试覆盖

| 测试 | 覆盖内容 |
|------|---------|
| test_single_sheet_writes_valid_zip | ZIP 合法，5 个必需文件存在 |
| test_single_sheet_name_preserved | 中文 sheet 名保留 |
| test_single_sheet_headers_parseable | 表头可通过 inlineStr 解析 |
| test_single_sheet_inline_str_cell_values | inlineStr 值正确 |
| test_multi_sheet_workbook | 多 sheet 顺序正确 |
| test_file_size_above_1kb_with_data | 大数据集文件大小 |
| test_empty_sheet_gets_empty_fallback_row | 空 sheet 处理 |
| test_chinese_sheet_names | 9 个中文 sheet 名全部保留 |
| test_chinese_cell_content | 中文单元格内容 |
| test_angle_brackets_escaped | `<` `>` 转义 |
| test_ampersand_escaped | `&` 转义 |
| test_double_quotes_in_cell | `"` 转义 |
| test_sheet_name_truncated_to_31_chars | 长名称截断 |
| test_no_legacy_import | AST 检查不含 legacy |
| test_no_web_import | AST 检查不含 web |
| test_no_openpyxl_import | AST 检查不含 openpyxl |
| test_no_shared_strings_xml | 无 sharedStrings.xml |
| test_no_styles_xml | 无 styles.xml |
| test_workbook_xml_parseable | workbook XML 合法 |
| test_all_numeric_data_preserved | 数值数据保留 |
