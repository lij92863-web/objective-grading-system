# Stage E4 HTML Exporter Migration Summary

> 完成日期：2026-07-09
> 阶段：E4A → E4B → E4C → E4D → E4E → E4F → E4G → E4H

## 本阶段目标

将 HTML 报告导出（simple_report.html, advanced_dashboard.html, index.html）从 legacy 迁到 `app/infrastructure/exporters/`。不改前端 UI，不改报告视觉格式。

## 迁移了哪些 HTML exporter

| Exporter | 文件 | 对应 legacy | 输出 |
|----------|------|-----------|------|
| `SimpleReportHtmlExporter` | `simple_report_html_exporter.py` | `write_simple_report` | `simple_report.html` |
| `AdvancedDashboardHtmlExporter` | `advanced_dashboard_html_exporter.py` | `write_advanced_dashboard` | `advanced_dashboard.html` |
| `ReportIndexHtmlExporter` | `report_index_html_exporter.py` | `write_report_index` | `index.html` |

支持库：
- `html_helpers.py` — 20+ 函数：html_escape, CSS, 渲染, 分析辅助

## Workflow 修改点

`app/workflow.py` — 3 处 HTML 调用替换：
- `legacy.write_simple_report(...)` → `SimpleReportHtmlExporter().export(...)`
- `legacy.write_advanced_dashboard(...)` → `AdvancedDashboardHtmlExporter().export(...)`
- `legacy.write_report_index(...)` → `ReportIndexHtmlExporter().export(...)`

## 新旧 HTML shadow 对比结果

E4F shadow parity：全部通过（12 tests）。

| 对比维度 | 结果 |
|---------|------|
| 文件名 | ✅ 一致 |
| 标题 | ✅ 一致 |
| 核心 section | ✅ 一致 |
| 链接 | ✅ 一致 |
| 中文 | ✅ 不乱码 |
| 文件大小 | ✅ 合理 |

## 旧 CLI smoke 结果

✅ 通过（`python objective_grader.py ...` → returncode=0，3 HTML + 8 CSV + 2 Excel 正常）

## HTML 文件名

- `simple_report.html` — 普通版报告
- `advanced_dashboard.html` — 高级学情分析
- `index.html` — 报告首页

## 链接关系

```
index.html → simple_report.html (btn-primary)
index.html → advanced_dashboard.html (btn-success)
index.html → simple_score_report.xlsx (btn-outline)
simple_report.html → simple_score_report.xlsx
```

## 哪些 legacy HTML 调用已移除

- ✅ `legacy.write_simple_report`
- ✅ `legacy.write_advanced_dashboard`
- ✅ `legacy.write_report_index`

## 当前 legacy 剩余内容

- 判分核心 re-export（QuestionSpec, AnswerKey, grade_all 等）
- CSV 加载（load_answer_key, load_submissions, load_question_bank）
- 简单数据函数（simple_score_rows, item_stats, basic_stats — 仍有 workflow 依赖）
- 旧 CLI main() 函数
- 归档逻辑（archive_reports）
- old_modules/ 旧代码存档

## 当前仍存在风险

| 风险 | 等级 | 说明 |
|------|------|------|
| workflow 仍调用 legacy 计算函数 | 低 | simple_score_rows, item_stats 仍在 workflow 中用来生成 rows |
| legacy 未删除 | 低 | old_modules/ 可后续清理 |

## 下一步 legacy 瘦身建议

1. simple_score_rows / item_stats 可迁到 app/application/use_cases/report_builders/
2. old_modules/ 可考虑归档删除
3. legacy CLI main() 可精简为纯 facade
