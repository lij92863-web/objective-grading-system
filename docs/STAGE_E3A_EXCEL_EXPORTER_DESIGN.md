# Stage E3A — Excel Exporter Design

## 当前 Legacy Excel 行为

### 输出文件

| 文件 | 生成方式 | 输入 |
|------|---------|------|
| `exam_report.xlsx` | `write_enhanced_workbook` → fallback `legacy.write_workbook` | 9 个 CSV Path |
| `simple_score_report.xlsx` | `legacy.write_simple_score_workbook` | `simple_score_rows()` 输出的 dict list |

### exam_report.xlsx 的 9 个 sheet

| # | Sheet 名 | 数据来源 CSV |
|---|---------|-------------|
| 1 | 成绩总表 | summary.csv |
| 2 | 每题明细 | detail.csv |
| 3 | 每题分析 | item_analysis.csv |
| 4 | 知识点画像 | knowledge_profile.csv |
| 5 | 学生错题 | student_wrong.csv（workflow 新字段） |
| 6 | 讲评计划 | teaching_plan.csv（workflow 新字段） |
| 7 | 班级补救 | class_remedial_package.csv（workflow 新字段） |
| 8 | 分层补救 | layered_remedial_plan.csv（workflow 新字段） |
| 9 | 数据质量检查 | validation_report.csv |

### simple_score_report.xlsx 的 1 个 sheet

| Sheet 名 | 字段 |
|----------|------|
| scores | rank, student_id, name, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count, wrong_questions, blank_questions, remark |

### 数据来源

- **full workbook**: 数据来自 CSV 文件（summary, detail, item_analysis, knowledge_profile, student_wrong, teaching_plan, class_remedial, layered_remedial, validation_report）。CSV 由 `run_csv_report_pipeline` 生成。
- **simple score workbook**: 数据来自 `legacy.simple_score_rows(results)` 返回的 dict list。

### openpyxl 依赖

- **`write_enhanced_workbook`**（workflow.py L311-347）: 优先使用 openpyxl（带样式：header_fill, error_fill, warning_fill, freeze_panes, auto_filter, column_width）。openpyxl 不可用时 fallback 到 `legacy.write_workbook`（纯 Python ZIP+XML，无样式）。
- **`legacy.write_simple_score_workbook`**: 始终走 `legacy.write_xlsx`（纯 Python ZIP+XML），不依赖 openpyxl。
- **`legacy.write_workbook`**: 始终走 `legacy.write_xlsx`（纯 Python ZIP+XML），不依赖 openpyxl。
- **`legacy.write_xlsx`**: 纯 Python 实现，使用 `zipfile` + `xml.etree` 手工构造 XLSX，零外部依赖。

### openpyxl 不可用时的降级路径

当前版本（`write_enhanced_workbook`）已有 fallback：
```
try: import openpyxl; use enhanced (styled)
except ImportError: legacy.write_workbook (plain)
```

## 迁移策略

### 两个 exporter

| Exporter | 对应 legacy | 输出文件 |
|----------|-----------|---------|
| `SimpleScoreWorkbookExporter` | `legacy.write_simple_score_workbook` | `simple_score_report.xlsx` |
| `WorkbookExporter` | `legacy.write_workbook` / `write_enhanced_workbook` | `exam_report.xlsx` |

### 核心原则

1. **Excel exporter 只负责把已有 CSV / rows 包装成 xlsx**
2. 不在 exporter 里重新判分、重新分析、重新生成 report rows
3. Excel 是基础设施导出层，不是业务层
4. 不 import legacy，不 import web

### 输入策略

| Exporter | 输入 |
|----------|------|
| SimpleScoreWorkbookExporter | dict list（与 `simple_score_rows` 输出格式一致） |
| WorkbookExporter | CSV 文件路径 list（每项 = (sheet_name, csv_path)） |

### 输出格式

- 优先使用 openpyxl（提供样式），openpyxl 不可用时使用纯 Python ZIP+XML 降级
- 文件名必须与 legacy 一致
- Sheet 名必须与 legacy 一致
- 表头必须与 legacy 一致
- 核心内容必须与 legacy 一致

## 测试策略

### E3A 行为加固测试（当前阶段）

- **文件存在 + 大小 + 扩展名**：基础烟雾测试
- **ZIP 校验**：验证 XLSX 是有效 ZIP
- **Sheet 名称 + 数量**：通过 ZIP + XML 解析
- **表头内容**：通过 ZIP + XML 解析
- **行数检查**：至少 header + 数据
- **中文不乱码**：XML 内直接检查
- **openpyxl 深度测试**：仅 openpyxl 可用时运行

### E3B 简单 workbook exporter 测试

- 新 exporter 输出 vs legacy 输出对比（sheet 名、表头、行数、首行数据）
- 不 import legacy、不调用真实 API

### E3C 完整 workbook exporter 测试

- 与 E3B 类似，覆盖所有 9 个 sheet

### E3D shadow parity

- 同一份数据分别走 legacy 和新 exporter，对比输出

## openpyxl 不可用时的限制

**当前环境 openpyxl 不可用**（`ModuleNotFoundError: No module named 'openpyxl'`）。

影响：
1. 无法进行 openpyxl 深度测试（单元格样式、列宽、字体等）
2. 测试通过 ZIP + XML 解析进行，能覆盖 sheet 名、表头、行数、中文编码
3. E3A 阶段不新增依赖（按任务要求）
4. 新 exporter 设计需要两种模式：openpyxl 可用时用 openpyxl，不可用时用纯 Python

**重要**：按照任务文档，openpyxl 不可用时 E3B 应停止。文档已明确此限制。

## 进入 E3B 的条件

1. ✅ E3A 所有测试通过
2. ❌ openpyxl 深度检查可用 — **当前不满足**
3. 按任务文档要求：**openpyxl 不可用，停止 E3B，不要强行迁**

## 后续建议

1. 安装 openpyxl：`pip install openpyxl`
2. 重新运行 E3A 测试确认深度检查通过
3. 然后进入 E3B
