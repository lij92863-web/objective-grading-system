# Stage E3A-H — Excel 依赖与实现路线审计

> 审计日期：2026-07-09
> 审计范围：legacy Excel 实现、项目依赖、E3B-E3F 技术路线
> 前提：未安装 openpyxl，未修改 legacy/workflow/exporter/UI

---

## 一、Legacy 当前 Excel 实现方式

### 1.1 核心结论

**Legacy 完全不依赖 openpyxl、xlsxwriter、pandas、xlwt、xlrd 等任何第三方 Excel 库。**

Excel（.xlsx）生成完全使用 Python 标准库 `zipfile` + `xml.sax.saxutils.escape` 手工构造。

### 1.2 逐项回答

| 问题 | 答案 | 证据 |
|------|------|------|
| legacy 是否 import openpyxl？ | **否** | `grep` 无匹配；`ast.parse` 审计通过 `test_legacy_does_not_import_openpyxl` |
| legacy 是否 import xlsxwriter？ | **否** | `grep` 无匹配；`test_legacy_does_not_import_xlsxwriter` 通过 |
| legacy 是否 import pandas？ | **否** | `grep` 无匹配；`test_legacy_does_not_import_pandas` 通过 |
| legacy 是否用 zipfile + XML 手写 xlsx？ | **是** | `write_xlsx()` 使用 `zipfile.ZipFile` + `worksheet_xml()` 生成 XML |
| legacy 是否使用 csv → xlsx 的转换？ | **是** | `write_workbook()` → `read_csv_for_workbook()` → `write_xlsx()` |
| legacy 是否依赖已有 CSV 文件生成 workbook？ | **是** | `write_workbook(path, report_files)` 接收 `List[Tuple[str, Path]]`，每个 tuple 是 (sheet_name, csv_path) |
| legacy 是否重新计算 report data？ | **否** | `write_workbook` 只读取已有 CSV；`write_simple_score_workbook` 只接收已计算的 dict list |
| legacy Excel 和 CSV 的关系是什么？ | **Excel 是 CSV 的 ZIP+XML 包装** | `write_workbook` 读 CSV → 转 `List[List[str]]` → `write_xlsx` 写出 xlsx |

### 1.3 Legacy Excel 相关函数详解

#### `write_xlsx(path, sheets)` — L1142-1193
纯 Python 实现，零外部依赖。

```
输入: path (Path), sheets (List[Tuple[str, List[List[str]]]])
输出: .xlsx 文件（ZIP 容器）

内部构造:
  [Content_Types].xml     — MIME 类型声明
  _rels/.rels             — 根关系文件
  xl/workbook.xml         — 工作簿定义 + sheet 列表
  xl/_rels/workbook.xml.rels — 工作表关系
  xl/worksheets/sheetN.xml   — 每个 sheet 的单元格数据（inlineStr）
```

关键特征：
- 所有单元格使用 `t="inlineStr"`（不使用 sharedStrings）
- 无 `xl/styles.xml`（无样式）
- 无 `xl/theme/`（无主题）
- 无列宽、无冻结窗格、无公式
- 压缩方式：`zipfile.ZIP_DEFLATED`

#### `worksheet_xml(rows)` — L1121-1135
将 `List[List[str]]` 转为 OOXML worksheet XML。

- 每个 cell 为 `<c r="A1" t="inlineStr"><is><t>{text}</t></is></c>`
- 使用 `xml.sax.saxutils.escape()` 转义特殊字符

#### `write_workbook(path, report_files)` — L1196-1198
```
for sheet_name, csv_path in report_files:
    rows = read_csv_for_workbook(csv_path)  # csv.reader → List[List[str]]
write_xlsx(path, sheets)
```

#### `write_simple_score_workbook(path, rows)` — L1302-1319
```
fields = ["rank", "student_id", "name", ...]
sheet_rows = [fields] + [[str(row.get(f, "")) for f in fields] for row in rows]
write_xlsx(path, [("scores", sheet_rows)])
```

#### `read_csv_for_workbook(path)` — L1106-1110
```python
with path.open("r", encoding="utf-8-sig", newline="") as handle:
    return [list(row) for row in csv.reader(handle)]
```

### 1.4 Workflow 中的 openpyxl 增强路径

`app/workflow.py:write_enhanced_workbook()` (L311-347)：

```python
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    legacy.write_workbook(path, report_files)  # ← 降级到纯 Python
    return

# openpyxl 可用时：带样式（header_fill, error_fill, warning_fill,
#                        freeze_panes, auto_filter, column_width）
```

**结论：openpyxl 是可选增强，不是必需依赖。** 降级路径 `legacy.write_workbook` 始终可用。

---

## 二、项目依赖文件审计

### 2.1 审计结果

| 文件 | 是否存在 |
|------|---------|
| `requirements.txt` | **否** |
| `pyproject.toml` | **否** |
| `setup.py` | **否** |
| `setup.cfg` | **否** |
| `Pipfile` | **否** |
| `poetry.lock` | **否** |
| `environment.yml` | **否** |

### 2.2 Excel 依赖声明状态

| 库 | 是否在依赖文件中声明 |
|----|-------------------|
| openpyxl | **否**（无依赖文件可声明） |
| xlsxwriter | **否** |
| pandas | **否** |
| xlwt | **否** |
| xlrd | **否** |

### 2.3 结论

**项目当前无任何依赖文件，因此无任何 Excel 库声明。** 项目为标准 Python 3 标准库即可运行（判分、CSV 生成、Excel 生成、HTML 生成全部使用标准库）。

唯一需要第三方库的功能：
- `openpyxl`：仅用于 `write_enhanced_workbook` 的**带样式 Excel** 输出（可选）
- 千问 API 相关（`dashscope`）：仅用于 OCR 识别（不在本次审计范围）

---

## 三、当前环境为什么能生成 xlsx（openpyxl 不可用时）

### 3.1 原因

**Legacy 实现了完全自足的纯 Python ZIP+XML XLSX 生成器**，不依赖任何第三方 Excel 库。

调用链（openpyxl 不可用时）：

```
run_grading()
  └─ write_enhanced_workbook()
       └─ import openpyxl → ImportError
            └─ legacy.write_workbook()         ← 纯 Python 降级路径
                 └─ read_csv_for_workbook()     ← csv.reader
                 └─ write_xlsx()                ← zipfile + xml
                      └─ worksheet_xml()        ← inlineStr XML
  └─ legacy.write_simple_score_workbook()
       └─ write_xlsx()                         ← 始终纯 Python
```

### 3.2 不是以下原因

| 猜测 | 是否为真 | 说明 |
|------|---------|------|
| 使用了其他已安装库？ | **否** | `pip list` 可确认无 openpyxl/xlsxwriter/pandas |
| 测试只检查到了文件但不是完整 xlsx？ | **否** | 测试验证了 ZIP 结构、sheet 名、表头、行数、中文编码 — 是完整合法的 xlsx |
| 某个 fallback 生效？ | **是 — 这是正确原因** | `write_enhanced_workbook` 的 `except ImportError` fallback |

### 3.3 验证

- `python -c "import openpyxl"` → `ModuleNotFoundError`
- `test_xlsx_are_valid_zip_archives` → 通过（ZIP 合法）
- `test_full_workbook_sheet_names_match_legacy` → 通过（9 个 sheet 名称正确）
- `test_full_workbook_key_sheet_headers_match_legacy` → 通过（表头正确）
- `test_full_workbook_chinese_not_garbled` → 通过（中文编码正确）

---

## 四、Excel 输出结构

### 4.1 exam_report.xlsx（完整工作簿）

| 属性 | 值 |
|------|-----|
| 文件名 | `exam_report.xlsx` |
| Sheet 数量 | **9** |
| 是否有样式 | **否**（无 openpyxl 时） |
| 是否有列宽 | **否** |
| 是否有冻结窗格 | **否** |
| 是否有公式 | **否** |
| 是否多工作簿 | **否**（单个 workbook） |
| 单元格值方式 | **inlineStr**（非 sharedStrings） |
| 压缩方式 | ZIP_DEFLATED |

#### Sheet 列表

| # | Sheet 名 | 数据来源 CSV | 数据来源说明 |
|---|---------|-------------|-------------|
| 1 | 成绩总表 | summary.csv | 学生成绩汇总（student_id, name, rank, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count） |
| 2 | 每题明细 | detail.csv | 每题得分明细（student_id, name, question, question_id, question_status, difficulty, tags, expected, actual, raw_actual, score, max_score, status） |
| 3 | 每题分析 | item_analysis.csv | 每题统计（question, question_id, question_status, difficulty, tags, answer, points, accuracy, blank_rate, wrong_rate, partial_rate, invalid_rate, option_distribution） |
| 4 | 知识点画像 | knowledge_profile.csv | 知识点掌握情况（student_id, name, tag, score, max_score, mastery, mastery_level, question_count, weak） |
| 5 | 学生错题 | student_wrong_list.csv | 学生错题清单（student_id, name, wrong_questions, partial_questions, blank_questions, invalid_questions） |
| 6 | 讲评计划 | teaching_plan.csv | 讲评优先级（priority_level, question_id, accuracy, blank_rate, main_wrong_answer, tags, reason, teaching_suggestion） |
| 7 | 班级补救 | class_remedial_package.csv | 班级补救练习（weak_tag, related_questions, class_accuracy, affected_student_count, recommended_question_ids, suggested_difficulty, teaching_note） |
| 8 | 分层补救 | layered_remedial_plan.csv | 分层补救建议（layer_name, score_range, student_count, suggested_task, recommended_question_ids, teacher_note） |
| 9 | 数据质量检查 | validation_report.csv | 数据校验（severity, scope, item, message） |

### 4.2 simple_score_report.xlsx（简单成绩表）

| 属性 | 值 |
|------|-----|
| 文件名 | `simple_score_report.xlsx` |
| Sheet 数量 | **1** |
| Sheet 名 | `scores` |
| 字段（13 列） | rank, student_id, name, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count, wrong_questions, blank_questions, remark |
| 数据来源 | `legacy.simple_score_rows(results)` 返回的 dict list |
| 是否有样式 | **否** |

---

## 五、Recommended E3B-E3F Route

### 5.1 路线判断：Route B

| 路线 | 描述 | 是否适用 |
|------|------|---------|
| Route A | legacy 已使用 openpyxl，依赖文件声明 openpyxl | **不适用** — legacy 不使用 openpyxl |
| **Route B** | **legacy 不使用 openpyxl，使用标准库 zipfile/xml** | ✅ **适用** |
| Route C | legacy 使用 xlsxwriter/pandas | **不适用** |
| Route D | 实现混乱，无法确认 | **不适用** — 实现清晰明确 |

### 5.2 推荐技术路线

**E3B-E3F 应沿用标准库 zipfile/xml 路线，不应新增 openpyxl 依赖。**

核心原则：

1. **不引入新依赖** — 项目当前零依赖即可生成完整 xlsx，迁移不应改变这一点
2. **优先沿用 legacy 现有技术路线** — `zipfile` + `xml.etree` + `inlineStr` 已被验证可行
3. **新 exporter 不 import legacy** — 独立实现，不耦合
4. **新 exporter 不重新计算数据** — 只接收已有 CSV/rows 作为输入
5. **新 exporter 不改 sheet 名、表头、核心内容** — 输出与 legacy 完全一致
6. **没有足够测试前不切 workflow** — shadow parity 必须先通过

### 5.3 SimpleScoreWorkbookExporter 实现建议

```
输入: List[Dict[str, object]]  （与 simple_score_rows 输出格式一致）
输出: simple_score_report.xlsx

实现:
  1. 接收 fields = ["rank", "student_id", "name", ...]
  2. 构建 sheet_rows = [fields] + [数据行]
  3. 调用通用的 write_xlsx(path, [("scores", sheet_rows)])
  4. 使用 zipfile + inlineStr（与 legacy 一致）
```

### 5.4 WorkbookExporter 实现建议

```
输入: List[Tuple[str, Path]]  （sheet_name, csv_path）
输出: exam_report.xlsx

实现:
  1. 对每个 csv_path 调用 csv.reader 读取 rows
  2. 调用通用的 write_xlsx(path, sheets)
  3. 使用 zipfile + inlineStr（与 legacy 一致）
  4. 9 个 sheet 名称和顺序与 legacy 完全一致
```

### 5.5 新旧对比方法

- **E3D shadow parity**：同一份 demo 数据分别走 legacy 和新 exporter
- 对比维度：sheet 名、表头、行数、每行每列值、ZIP 内部文件列表
- 使用 `zipfile` + `xml.etree` 解析两端输出逐项对比（不依赖 openpyxl）

### 5.6 Workflow 切换条件

**必须满足以下全部条件才能切 workflow：**

1. ✅ E3A 行为测试全部通过（已满足）
2. ⬜ `SimpleScoreWorkbookExporter` 实现完成并通过测试（E3B）
3. ⬜ `WorkbookExporter` 实现完成并通过测试（E3C）
4. ⬜ E3D shadow parity 全部通过
5. ⬜ workflow guard 测试更新（拦截误调用 legacy.write_workbook）
6. ⬜ 完整测试套件通过（`python run_tests.py` 零失败）

### 5.7 停止条件

以下情况必须停止，不可继续 E3B-E3F：

1. 需要安装 openpyxl 才能继续 → **不适用**（本路线不需要）
2. 需要修改 legacy 才能继续 → **停止**
3. 需要修改 workflow 中 CSV pipeline 才能继续 → **停止**
4. 需要改变 sheet 名、表头、字段才能继续 → **停止**
5. shadow parity 不通过 → **停止并报告差异**
6. 测试失败无法在本阶段修复 → **停止**

---

## 六、Next Task Draft（E3B-E3F 草案）

> **本草案基于 Route B（标准库 zipfile/xml），无需安装 openpyxl。**

### E3B: SimpleScoreWorkbookExporter

**目标**：实现 `app/infrastructure/exporters/simple_score_workbook_exporter.py`

- 输入：`List[Dict[str, object]]`（dict list，字段与 `simple_score_rows` 输出一致）
- 输出：`simple_score_report.xlsx`
- 技术路线：`zipfile` + `xml.etree` + `inlineStr`（与 legacy.write_xlsx 同路线）
- 实现：独立的 `write_xlsx` 通用函数（可放在 `app/infrastructure/exporters/_xlsx_helpers.py`）
- 测试：与 legacy 输出对比（sheet 名、表头、行数、首行数据）
- 不 import legacy
- 不 import openpyxl

### E3C: WorkbookExporter

**目标**：实现 `app/infrastructure/exporters/workbook_exporter.py`

- 输入：`List[Tuple[str, Path]]`（sheet_name, csv_path）
- 输出：`exam_report.xlsx`（9 个 sheet）
- 技术路线：复用 E3B 中的 `write_xlsx` 通用函数
- 测试：与 legacy 输出对比（全部 9 个 sheet）
- 不 import legacy
- 不 import openpyxl

### E3D: Shadow Parity

**目标**：同一份 demo 数据分别走 legacy 和新 exporter，逐项对比

- 将新 exporter 的输出与 legacy 输出做 ZIP 级别对比
- 对比维度：ZIP 内容列表、sheet 名称、表头、行数、每行每列的值
- 使用标准库 `zipfile` + `xml.etree`（不依赖 openpyxl）
- 全部通过后记录 parity report

### E3E: Workflow 切换

**目标**：`app/workflow.py` 中 `write_enhanced_workbook` 改为调用新 exporter

- 保留 openpyxl 增强路径（openpyxl 可用时优先使用，作为可选的增强模式）
- 降级路径改为新 exporter（而非 legacy.write_workbook）
- Guard 测试更新
- 不再直接调用 `legacy.write_workbook` / `legacy.write_simple_score_workbook`

### E3F: 清理与文档

- 更新 `docs/EXPORTER_MIGRATION_AUDIT.md`
- 更新 `docs/LEGACY_QUARANTINE_LEDGER.md`
- 确认所有测试通过
- 确认 git status 干净

---

## 七、附录：当前测试覆盖矩阵

### 已有测试（E3A test_excel_legacy_behavior.py）

| 测试 | 覆盖内容 | 状态 |
|------|---------|------|
| test_excel_files_exist_and_non_empty | 文件存在、大小 > 1KB、.xlsx 扩展名 | ✅ |
| test_xlsx_are_valid_zip_archives | ZIP 合法、workbook.xml、Content_Types.xml | ✅ |
| test_full_workbook_sheet_names_match_legacy | 9 个 sheet 名称 | ✅ |
| test_full_workbook_has_nine_sheets | sheet 数量 = 9 | ✅ |
| test_full_workbook_every_sheet_has_header | 每个 sheet 有表头 | ✅ |
| test_full_workbook_key_sheet_headers_match_legacy | 核心 sheet 表头 | ✅ |
| test_full_workbook_has_student_data_rows | 数据行数 > 1 | ✅ |
| test_full_workbook_chinese_not_garbled | 中文 sheet 名编码 | ✅ |
| test_full_workbook_worksheets_xml_exist | xl/worksheets/*.xml 存在 | ✅ (本次新增) |
| test_full_workbook_inlinestr_not_sharedstrings | inlineStr 机制存在 | ✅ (本次新增) |
| test_full_workbook_no_styles_xml | 无 styles.xml | ✅ (本次新增) |
| test_full_workbook_inlinestr_cell_values_parseable | inlineStr 值可解析 | ✅ (本次新增) |
| test_simple_score_workbook_sheet_name | scores sheet | ✅ |
| test_simple_score_workbook_header_matches_legacy | 13 列表头 | ✅ |
| test_simple_score_workbook_has_data_rows | 数据行 | ✅ |
| test_simple_score_workbook_worksheets_xml_exist | worksheet XML | ✅ (本次新增) |
| test_excel_opens_with_openpyxl | openpyxl 深度检查 | ⏭ skipped |
| test_simple_score_opens_with_openpyxl | openpyxl 深度检查 | ⏭ skipped |
| test_no_api_called | 不调真实 API | ✅ |
| test_no_legacy_imports_in_existing_exporters | exporter 不引 legacy | ✅ |

### 新增测试（E3A-H test_excel_dependency_audit.py）

| 测试 | 覆盖内容 | 状态 |
|------|---------|------|
| test_dependency_files_present_or_absent | 依赖文件清单 | ✅ |
| test_no_excel_library_in_requirements_txt | requirements.txt 审计 | ⏭ skipped（无文件） |
| test_no_excel_library_in_pyproject_toml | pyproject.toml 审计 | ⏭ skipped（无文件） |
| test_no_excel_library_in_setup_cfg | setup.cfg 审计 | ⏭ skipped（无文件） |
| test_legacy_does_not_import_openpyxl | legacy 不含 openpyxl | ✅ |
| test_legacy_does_not_import_xlsxwriter | legacy 不含 xlsxwriter | ✅ |
| test_legacy_does_not_import_pandas | legacy 不含 pandas | ✅ |
| test_legacy_does_not_import_xlwt | legacy 不含 xlwt | ✅ |
| test_legacy_does_not_import_xlrd | legacy 不含 xlrd | ✅ |
| test_legacy_uses_zipfile_for_xlsx | legacy 使用 zipfile | ✅ |
| test_legacy_uses_xml_for_xlsx | legacy 使用 xml | ✅ |
| test_openpyxl_availability_is_recorded | openpyxl 状态记录 | ✅ |
| test_openpyxl_not_required_for_tests | 不要求 openpyxl | ✅ |
| test_workflow_has_openpyxl_fallback | workflow 有降级 | ✅ |
| test_workflow_fallback_calls_legacy_write_workbook | fallback 调用正确 | ✅ |

---

## 八、审计结论摘要

1. **Legacy Excel 实现**：纯 Python 标准库 `zipfile` + `xml`，零外部依赖
2. **项目依赖**：无任何依赖文件，无任何 Excel 库声明
3. **无 openpyxl 仍能生成 xlsx**：`write_enhanced_workbook` 的 `except ImportError` fallback 到 `legacy.write_workbook`（纯 Python）
4. **推荐路线**：Route B — 沿用标准库 zipfile/xml 路线，不新增 openpyxl 依赖
5. **可以无 openpyxl 继续 E3B**：是
6. **Excel 输出结构**：9+1 sheet，inlineStr 单元格，无样式/列宽/冻结窗格/公式
