# Stage E4A — HTML Exporter Audit

> 审计日期：2026-07-09
> 范围：legacy HTML 报告导出函数

## 一、Legacy HTML 函数清单

### 主输出函数（workflow 直接调用）

| 函数 | 输出文件 | 输入 | L |
|------|---------|------|----|
| `write_simple_report` | `simple_report.html` | meta, answer_key, results, simple_rows, item_rows | 1359 |
| `write_advanced_dashboard` | `advanced_dashboard.html` | meta, results, profiles, validation_rows, item_rows | 1653 |
| `write_report_index` | `index.html` | meta, simple_report_path, advanced_dashboard_path, simple_score_report_path | 1701 |

### 渲染辅助函数

| 函数 | 用途 | L |
|------|------|----|
| `html_escape` | HTML 转义 (`&`, `<`, `>`, `"`, `'`) | 1201 |
| `pct` | 百分比格式 `"95.00%"` | 1205 |
| `percent` | 百分比格式（带异常处理） | 1409 |
| `render_table` | HTML `<table>` 渲染 | 1322 |
| `bar` | 简单水平条形图 HTML | 1330 |
| `report_link` | 条件链接或禁用按钮 | 1695 |
| `report_css` | 简单报告 CSS | 1341 |
| `advanced_dashboard_css` | Dashboard CSS | 1546 |
| `get_rate_class` | 正确率 → CSS class | 1416 |
| `render_metric_cards` | 指标卡网格 | 1569 |
| `render_vertical_bar_chart` | 垂直柱状图 | 1576 |
| `render_horizontal_bar_chart` | 水平条形图 | 1592 |
| `render_wrong_top` | 易错题卡片列表 | 1604 |
| `render_abnormal_table` | 答题异常表格 | 1615 |
| `render_suggestion_cards` | 教学建议卡片 | 1627 |
| `render_option_distribution` | 选项分布网格 | 1636 |

### 分析辅助函数（供渲染调用）

| 函数 | 用途 | L |
|------|------|----|
| `basic_stats` | 从 results 计算平均分/最高/最低/及格率/优秀率 | 1209 |
| `score_bands` | 分数段统计 | 1291 |
| `build_score_distribution` | 构建分布图数据 | 1430 |
| `build_question_accuracy_items` | 每题正确率数据 | 1434 |
| `main_wrong_answer` | 找出主要错误答案 | 1442 |
| `build_weak_items` | 易错题 Top N | 1459 |
| `build_weak_tags` | 薄弱知识点 Top N | 1483 |
| `build_abnormal_items` | 答题异常检测 | 1494 |
| `build_teaching_suggestions` | 生成教学建议 | 1520 |

### 其他依赖

| 函数 | 用途 | L |
|------|------|----|
| `safe_slug` | 文件名安全化（archive 用，HTML 不直接用） | 1756 |
| `archive_reports` | 归档（workflow 用，非 HTML 专属） | 1763 |

## 二、每个 HTML 核心结构

### simple_report.html

```
<!doctype html>
<html lang="zh-CN">
<head> 标题: "普通版报告 - {exam_name}" + report_css()
<body>
  <h1>普通版报告</h1>
  <p> 考试名 · 班级 · 日期
  <div> 链接到 simple_score_report.xlsx
  <section> 6 个指标卡：参考人数、平均分、最高分、最低分、及格率、优秀率
  <table> 学生成绩表（10 列）
  <section> 每题正确率柱状图 + 表格
  <table> 错得最多的题 Top 5
```

输入数据流：
- `basic_stats(results)` → 6 个指标
- `simple_rows` → 成绩表
- `item_rows` → 正确率柱 + 每题正确率表 + Top 5 错题

### advanced_dashboard.html

```
<!doctype html>
<html lang="zh-CN">
<head> 标题: "高级学情分析报告 - {exam_name}" + advanced_dashboard_css()
<body>
  <header> 考试名 · 班级 · 科目 · 日期 · 生成时间
  <section> 6 个指标卡
  <section> 8 个卡片：成绩分布、每题正确率、易错题 Top 5、薄弱知识点、
            答题异常、教学建议、选项分布、数据提醒
```

输入数据流：
- `basic_stats(results)` → 指标卡
- `score_bands(results)` → 成绩分布
- `item_rows` → 每题正确率、易错题、异常、选项分布
- `profiles` → 薄弱知识点
- `item_rows + profiles` → 教学建议
- `validation_rows` → 数据提醒表

### index.html

```
<!DOCTYPE html>
<html lang="zh-CN">
<head> 标题: "批改完成" + inline CSS
<body>
  <div> 卡片含考试元信息
  <div> 3 个链接按钮：simple_report.html, advanced_dashboard.html, simple_score_report.xlsx
```

## 三、CSS 来源

| 报告 | CSS | 位置 |
|------|-----|------|
| simple_report.html | `report_css()` 内联 | legacy L1341 |
| advanced_dashboard.html | `advanced_dashboard_css()` 内联 | legacy L1546 |
| index.html | 内联 CSS 字符串 | legacy L1715-1728 |

所有 CSS 均为内联 `<style>` 块，无外部 CSS 文件。

## 四、JS 是否存在

**否。** 三个 HTML 报告均不含 `<script>` 标签，无任何 JavaScript。

## 五、链接关系

```
index.html
  ├── → simple_report.html     (btn-primary)
  ├── → advanced_dashboard.html (btn-success)
  └── → simple_score_report.xlsx (btn-outline)

simple_report.html
  └── → simple_score_report.xlsx (actions button)

advanced_dashboard.html
  └── (无外部链接)
```

## 六、迁移风险

| 风险 | 等级 | 说明 |
|------|------|------|
| CSS 文本漂移 | 中 | 如果手动重写 CSS 字符串可能不一致，必须原样迁移 |
| 标题/链接变化 | 中 | 必须精确匹配 |
| 内联样式动态计算 | 低 | width/height 值基于数据，只比较结构 |
| 生成时间 `generated_at` | 低 | 每次不同，shadow parity 需排除时间字段 |
| 表格行数依赖数据 | 低 | demo 数据固定，输出稳定 |
| `build_*` 分析函数在 exporter 中 | 中 | 需要决定放 helper 还是 exporter 内 |

## 七、Shadow Parity 策略

对于每个 HTML 文件：
1. 规范化空白（压缩连续空白/换行）
2. 移除时间戳（`generated_at`）后比较
3. 比较：标题、关键 section 文本、链接 href、表头文本
4. 比较 CSS 文本（精确匹配）
5. 比较核心 DOM 结构（使用正则提取关键元素）

## 八、不迁 web/static/app.js 的原因

`web/static/app.js` 是 Web 前端应用 UI 的 JavaScript，不是导出的报告 HTML。本次任务只迁移"导出的 HTML 报告"，不涉及前端应用。三个报告 HTML 不含 `<script>` 标签，无 JS 依赖。
