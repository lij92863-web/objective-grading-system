# Exporter Migration Audit

## 审计目标

锁定 legacy 中所有与报告生成、Excel 导出、HTML dashboard 输出相关的函数，为迁移到 `app/infrastructure/exporters/` 做准备。

## 1. Legacy 输出函数清单

### CSV 输出（由 `app/workflow.py:run_grading()` 调用）

| 函数 | 输入 | 输出文件 | 依赖数据结构 |
|------|------|---------|-------------|
| `write_summary(path, results)` | StudentResult list | `summary.csv` | StudentResult |
| `write_detail(path, answer_key, results)` | AnswerKey, StudentResult list | `detail.csv` | AnswerKey, StudentResult, QuestionResult |
| `write_item_analysis(path, answer_key, results)` | AnswerKey, StudentResult list | `item_analysis.csv` | AnswerKey, StudentResult |
| `write_knowledge_profiles(path, profiles)` | KnowledgeProfile list | `knowledge_profile.csv` | KnowledgeProfile |
| `write_practice_recommendations(path, rows)` | dict list | `practice_recommendations.csv` | dict |
| `write_class_report(path, class_rows)` | dict list | `class_report.csv` | dict |
| `write_validation_report(path, validation_rows)` | dict list | `validation_report.csv` | dict |
| `write_student_report(path, results, profiles)` | StudentResult, KnowledgeProfile | `student_report.csv` | StudentResult, KnowledgeProfile |

### 分析函数（构建数据→供 CSV 输出）

| 函数 | 输入 | 输出 |
|------|------|------|
| `build_knowledge_profiles(answer_key, results)` | AnswerKey, StudentResult | KnowledgeProfile list |
| `build_class_report(answer_key, results, profiles, meta)` | AnswerKey, StudentResult, KnowledgeProfile, ExamMeta | dict list |
| `build_validation_report(answer_key, submissions, results, profiles, bank)` | AnswerKey, Submission, StudentResult, KnowledgeProfile, BankQuestion | dict list |
| `build_correct_question_ids(answer_key, results)` | AnswerKey, StudentResult | set of question_ids |
| `build_target_difficulties(answer_key, results)` | AnswerKey, StudentResult | dict |
| `recommend_practice(profiles, bank, per_tag, already_correct, target_difficulties)` | KnowledgeProfile, BankQuestion, sets | dict list |
| `simple_score_rows(results)` | StudentResult list | dict list |
| `item_stats(answer_key, results)` | AnswerKey, StudentResult | dict list |

### Excel 输出

| 函数 | 输入 | 输出文件 |
|------|------|---------|
| `write_workbook(path, report_files)` | list of (name, csv_path) | `exam_report.xlsx` |
| `write_simple_score_workbook(path, simple_rows)` | dict list | `simple_score_report.xlsx` |
| `write_xlsx(path, sheets)` | dict | arbitrary .xlsx |

### HTML 输出

| 函数 | 输入 | 输出文件 |
|------|------|---------|
| `write_simple_report(path, meta, answer_key, results, simple_rows, item_rows)` | ExamMeta, AnswerKey, StudentResult, dict lists | `simple_report.html` |
| `write_advanced_dashboard(path, meta, results, profiles, validation_rows, item_rows)` | ExamMeta, StudentResult, KnowledgeProfile, validation rows, dict lists | `advanced_dashboard.html` |
| `write_report_index(path, meta, simple_report_path, advanced_dashboard_path, simple_score_path)` | ExamMeta, Paths | `index.html` |

### 辅助函数（被以上函数调用）

| 函数 | 用途 |
|------|------|
| `html_escape(text)` | HTML 转义 |
| `read_csv_for_workbook(path)` | 读 CSV 到 worksheet rows |
| `report_css()` | 简单报告 CSS |
| `advanced_dashboard_css()` | Dashboard CSS |
| `render_metric_cards`, `render_vertical_bar_chart`, etc. | Dashboard HTML 片段 |
| `render_table`, `bar`, `pct` | 报告渲染工具 |
| `build_score_distribution`, `build_weak_items`, etc. | Dashboard 数据分析 |
| `safe_slug(value)` | 文件名安全化 |
| `archive_reports(...)` | 归档 old_outputs |
| `print_console_report(...)` | 控制台输出 |
| `write_dicts`, `write_dicts_with_fields` | 通用 CSV 写入 |

## 2. app/workflow.py 调用 legacy 的位置

`run_grading()` 函数（L395-571）直接调用以下 legacy 函数：

```
legacy.write_summary           → summary.csv
legacy.write_detail            → detail.csv
legacy.write_item_analysis    → item_analysis.csv
legacy.write_knowledge_profiles → knowledge_profile.csv
legacy.write_practice_recommendations → practice_recommendations.csv
legacy.write_class_report      → class_report.csv
legacy.write_validation_report → validation_report.csv
legacy.write_student_report    → student_report.csv
legacy.build_knowledge_profiles
legacy.build_validation_report
legacy.build_class_report
legacy.build_correct_question_ids
legacy.build_target_difficulties
legacy.recommend_practice
legacy.simple_score_rows
legacy.item_stats
legacy.write_simple_score_workbook → simple_score_report.xlsx
legacy.write_workbook           → exam_report.xlsx
legacy.write_simple_report      → simple_report.html
legacy.write_advanced_dashboard → advanced_dashboard.html
legacy.write_report_index       → index.html
```

`app/workflow.py` 本身新增的（不依赖 legacy）：
- `build_teaching_plan(item_rows)` → `teaching_plan.csv/.html`
- `build_class_remedial_package(...)` → `class_remedial_package.csv/.html`
- `build_layered_remedial_plan(...)` → `layered_remedial_plan.csv/.html`
- `build_student_wrong_list(results)` → `student_wrong_list.csv`

## 3. app/analysis.py 和 app/reports.py 的 facade 角色

`app/analysis.py` re-export 了 15 个 legacy 函数（write_summary, write_detail, write_item_analysis, build_knowledge_profiles, etc.）。
`app/reports.py` re-export 了 9 个 legacy 函数（write_workbook, write_advanced_dashboard, write_report_index, etc.）。

它们是纯 facade — 无新增逻辑。

## 4. 用户可见输出（不能乱改）

| 输出文件 | 用户用途 |
|---------|---------|
| `summary.csv` | 成绩总表 |
| `detail.csv` | 每题明细 |
| `item_analysis.csv` | 每题分析 |
| `knowledge_profile.csv` | 知识点画像 |
| `class_report.csv` | 班级报告 |
| `student_report.csv` | 学生报告 |
| `student_wrong_list.csv` | 学生错题清单 |
| `teaching_plan.csv/.html` | 讲评计划 |
| `class_remedial_package.csv/.html` | 班级补救包 |
| `layered_remedial_plan.csv/.html` | 分层补救 |
| `exam_report.xlsx` | 综合 Excel |
| `simple_score_report.xlsx` | 简单成绩表 |
| `simple_report.html` | 简单网页报告 |
| `advanced_dashboard.html` | 高级学情看板 |
| `index.html` | 报告首页 |
| `validation_report.csv` | 数据质量检查 |
| `error_report.html` | 错误报告（阻塞时） |

## 5. 可迁移到 app/infrastructure/exporters 的逻辑

| 逻辑 | 目标文件 |
|------|---------|
| `write_summary` | `exporters/summary_exporter.py` |
| `write_detail` | `exporters/detail_exporter.py` |
| `write_item_analysis` | `exporters/item_analysis_exporter.py` |
| `write_knowledge_profiles` | `exporters/knowledge_exporter.py` |
| `write_class_report` | `exporters/class_report_exporter.py` |
| `write_student_report` | `exporters/student_report_exporter.py` |
| `write_workbook` | `exporters/workbook_exporter.py` |
| `write_simple_score_workbook` | `exporters/workbook_exporter.py` |
| `write_simple_report` | `exporters/simple_report_html.py` |
| `write_advanced_dashboard` | `exporters/dashboard_html.py` |
| `write_report_index` | `exporters/index_html.py` |
| `html_escape`, `render_*`, `*_css` | `exporters/_html_helpers.py` |
| `write_dicts`, `read_csv_for_workbook` | `exporters/_csv_helpers.py` |

## 6. 应留在 application/use_cases 的逻辑

| 逻辑 | 原因 |
|------|------|
| `build_knowledge_profiles` | 分析逻辑，不是输出 |
| `build_class_report` | 分析逻辑 |
| `build_validation_report` | 检查逻辑 |
| `build_correct_question_ids` | 分析逻辑 |
| `recommend_practice` | 分析逻辑 |
| `simple_score_rows` | 数据转换 |
| `item_stats` | 分析逻辑 |
| `build_teaching_plan` | 已在 app/workflow.py |
| `build_class_remedial_package` | 已在 app/workflow.py |
| `build_layered_remedial_plan` | 已在 app/workflow.py |

## 7. 迁移风险

| 风险 | 等级 | 对策 |
|------|------|------|
| Excel 格式变化 | 高 | 先锁行为测试，再迁移 |
| HTML dashboard 布局变 | 高 | 逐文件比对新旧输出 |
| CSV 字段名变化 | 中 | 字段名保持完全一致 |
| 排序/编码差异 | 中 | 保持 UTF-8-BOM 和排序 |
| 文件路径约定变化 | 低 | 输出目录由调用方传入 |
| 性能退化 | 低 | 简单 CSV/HTML 无性能瓶颈 |

## 8. 后续推荐迁移顺序

1. **helpers first**: `_csv_helpers.py`, `_html_helpers.py`（被所有 exporter 依赖）
2. **CSV exporters**: summary, detail, item_analysis（最简单的格式）
3. **Analysis CSV**: knowledge_profiles, class_report, student_report
4. **Excel**: workbook, simple_score_workbook
5. **HTML**: simple_report, advanced_dashboard（最复杂，最后迁移）
6. **index.html**: report_index

每步迁移后运行 `test_exporter_legacy_behavior` 确认回归。
