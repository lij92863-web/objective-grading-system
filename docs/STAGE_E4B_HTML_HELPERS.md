# Stage E4B — HTML Helpers

## 目标

将 legacy 中所有 HTML 渲染相关 helper 函数迁到 `app/infrastructure/exporters/html_helpers.py`，行为与 legacy 完全一致。

## 文件

- `app/infrastructure/exporters/html_helpers.py`
- `tests/test_html_helpers.py`

## 迁移的函数

| 类别 | 函数 |
|------|------|
| 文本 | `html_escape`, `safe_slug` |
| 格式化 | `pct`, `percent`, `get_rate_class` |
| 统计 | `basic_stats`, `score_bands` |
| 分析 | `build_score_distribution`, `build_question_accuracy_items`, `main_wrong_answer`, `build_weak_items`, `build_weak_tags`, `build_abnormal_items`, `build_teaching_suggestions` |
| 渲染 | `render_table`, `bar`, `report_link`, `render_metric_cards`, `render_vertical_bar_chart`, `render_horizontal_bar_chart`, `render_wrong_top`, `render_abnormal_table`, `render_suggestion_cards`, `render_option_distribution` |
| CSS | `report_css`, `advanced_dashboard_css`, `index_css` |

## 依赖

仅标准库：`xml.sax.saxutils`, `statistics`, `collections`, `datetime`, `re`, `pathlib`

## 测试覆盖（27 tests）

- 转义行为（7 tests）
- 格式化（5 tests）
- safe_slug（3 tests）
- render_table（2 tests）
- bar, report_link, CSS, guards
