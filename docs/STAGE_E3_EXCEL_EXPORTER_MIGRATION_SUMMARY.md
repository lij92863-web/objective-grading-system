# Stage E3 Excel Exporter Migration Summary

> 完成日期：2026-07-09
> 技术路线：Route B — 标准库 zipfile + xml（零外部依赖）
> 阶段：E3B0 → E3B1 → E3B2 → E3C → E3D → E3E → E3F

---

## 一、本阶段目标

将 Excel 导出（`exam_report.xlsx`、`simple_score_report.xlsx`）从 legacy 迁到 `app/infrastructure/exporters/`，遵循 Route B 路线：使用纯 Python 标准库 `zipfile` + `xml`，不引入 openpyxl/xlsxwriter/pandas 等任何第三方依赖。

## 二、Route B 标准库 zipfile+xml 结论

经 E3A-H 审计确认：
- legacy 完全不依赖 openpyxl/xlsxwriter/pandas
- legacy Excel 生成使用 `zipfile.ZipFile` + `xml.sax.saxutils.escape` + `inlineStr`
- 项目无任何依赖文件（无 requirements.txt / pyproject.toml / setup.py 等）
- 当前环境无 openpyxl，但 legacy 和 new exporter 均能正常生成 xlsx

## 三、迁移了哪些 Excel exporter

| Exporter | 文件 | 对应 legacy | 输入 | 输出 |
|----------|------|-----------|------|------|
| `write_xlsx` (helper) | `app/infrastructure/exporters/xlsx_helpers.py` | `legacy.write_xlsx` | `List[XlsxSheet]` | 任意 .xlsx |
| `SimpleScoreWorkbookExporter` | `app/infrastructure/exporters/simple_score_workbook_exporter.py` | `legacy.write_simple_score_workbook` | dict list | `simple_score_report.xlsx` |
| `WorkbookExporter` | `app/infrastructure/exporters/workbook_exporter.py` | `legacy.write_workbook` | `List[Tuple[str, Path]]` | `exam_report.xlsx` |

## 四、Workflow 修改点

`app/workflow.py` — 3 处修改：

1. **新增 import**：`ExportRequest`, `SimpleScoreWorkbookExporter`, `WorkbookExporter`
2. **simple score workbook 切换**：`legacy.write_simple_score_workbook(...)` → `SimpleScoreWorkbookExporter().export(...)`
3. **full workbook 切换**：`write_enhanced_workbook(...)` → `WorkbookExporter().export(...)`
4. **移除**：`write_enhanced_workbook` 函数定义（openpyxl 增强路径，已不再需要）

## 五、新旧 Excel shadow 对比结果

E3D shadow parity：**全部通过**（16 tests）。

| 对比维度 | 结果 |
|---------|------|
| 文件存在 | ✅ |
| ZIP 结构合法 | ✅ |
| sheet 名和顺序 | ✅ 完全一致 |
| sheet 数量 | ✅ 9 + 1 |
| 所有 sheet 表头 | ✅ 完全一致 |
| 核心 sheet 首行数据 | ✅ 完全一致 |
| 中文不乱码 | ✅ |
| 文件大小 | ✅ 均 > 1KB |

## 六、旧 CLI smoke 结果

`python objective_grader.py --answer-key ... --submissions ... --out-dir ... --no-archive` → **通过**（returncode=0）

## 七、Excel 文件名

| 文件 | 说明 |
|------|------|
| `exam_report.xlsx` | 完整工作簿（9 sheets） |
| `simple_score_report.xlsx` | 简单成绩表（1 sheet） |

## 八、Sheet 名列表

### exam_report.xlsx（9 sheets，顺序固定）

1. 成绩总表
2. 每题明细
3. 每题分析
4. 知识点画像
5. 学生错题
6. 讲评计划
7. 班级补救
8. 分层补救
9. 数据质量检查

### simple_score_report.xlsx（1 sheet）

1. scores（13 字段：rank, student_id, name, score, max_score, percent, correct_count, wrong_or_partial_count, blank_count, invalid_count, wrong_questions, blank_questions, remark）

## 九、核心内容对比

- 新旧 Excel 核心结构一致（sheet 名、顺序、表头、行数、首行数据均一致）
- 新旧 Excel 均使用 inlineStr（不使用 sharedStrings）
- 新旧 Excel 均无样式（无 styles.xml）

## 十、哪些 legacy Excel 调用已移除

从 `app/workflow.py` 中已移除：

- ✅ `legacy.write_simple_score_workbook` → 改用 `SimpleScoreWorkbookExporter`
- ✅ `legacy.write_workbook`（via `write_enhanced_workbook` fallback） → 改用 `WorkbookExporter`
- ✅ `write_enhanced_workbook` 函数定义 → 已删除

## 十一、哪些 legacy HTML 调用仍保留

- `legacy.write_simple_report` → 仍在使用
- `legacy.write_advanced_dashboard` → 仍在使用
- `legacy.write_report_index` → 仍在使用
- `legacy.write_teacher_html`（via workflow helper） → 仍在使用

## 十二、当前风险

| 风险 | 等级 | 说明 |
|------|------|------|
| openpyxl 增强样式丢失 | 低 | 当前环境无 openpyxl，本来就没有样式 |
| 如果后续安装 openpyxl | 中 | 需要单独评估是否恢复 styled path |
| HTML 仍在 legacy | 中 | 后续迁移任务 |
| legacy write_xlsx 仍存在 | 低 | 仅供 CLI `legacy.main()` 独立运行时使用 |

## 十三、当前已经拆掉的炸弹

| 炸弹 | 状态 |
|------|------|
| workflow 依赖 legacy Excel | ✅ 已解除 |
| 必须安装 openpyxl 才能生成 Excel | ✅ 不存在（Route B 零依赖） |
| write_enhanced_workbook 引入 openpyxl import | ✅ 已移除（不再需要） |
| Excel 生成逻辑在 legacy | ✅ 已迁出到 infrastructure/exporters |

## 十四、当前仍存在的炸弹

| 炸弹 | 状态 |
|------|------|
| HTML dashboard 在 legacy | 待后续迁移 |
| legacy 判分数据模型（StudentResult 等）散落 | 待 domain 层完全独立 |
| simple_score_rows 和 item_stats 仍在 legacy | 待 report_builders 覆盖 |

## 十五、下一步 HTML 迁移建议

1. 先迁 `write_simple_report`（简单版 HTML）
2. 再迁 `write_advanced_dashboard`（复杂版 HTML，含 CSS/图表）
3. 最后迁 `write_report_index`
4. 每一步 shadow parity → guard → 切换

---

## 十六、测试统计

| 阶段 | 新增测试 | 累计测试 | 状态 |
|------|---------|---------|------|
| 起始（E3A-H） | — | 359 | ✅ |
| E3B1 | +20 | 379 | ✅ |
| E3B2 | +11 | 390 | ✅ |
| E3C | +10 | 400 | ✅ |
| E3D | +16 | 416 | ✅ |
| E3E | +14 | 430 | ✅ |
| **最终** | **+75** | **430** | ✅ (skipped=5) |
