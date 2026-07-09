"""HTML report helpers — extracted from legacy with identical behaviour.

Does NOT import legacy, web, or any third-party library.
Pure stdlib: xml.sax.saxutils, statistics, collections, datetime, re.
"""

import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as _xml_escape


# ── text escaping ─────────────────────────────────────────────────────────

def html_escape(value: object) -> str:
    """Escape & < > " ' for safe HTML text content."""
    return _xml_escape(str(value), {'"': "&quot;", "'": "&#x27;"})

# Workflow.py's helper — kept here for convenience
_H_ESCAPE = html_escape  # alias for internal use


# ── formatting ────────────────────────────────────────────────────────────

def pct(value: float) -> str:
    """Format a float as a percentage string e.g. '95.00%'."""
    return f"{value:.2f}%"


def percent(value: object) -> str:
    """Format any value as a percentage, returning '0.00%' on failure."""
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def get_rate_class(value: object) -> str:
    """Map a percentage value to a CSS class name."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number < 40:
        return "danger"
    if number < 60:
        return "warning"
    if number < 80:
        return "normal"
    return "good"


# ── slug ──────────────────────────────────────────────────────────────────

def safe_slug(value: str) -> str:
    """Sanitize a string for use in filenames/directory names."""
    text = (value or "exam").strip().lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_\-一-鿿]+", "", text)
    return text or "exam"


# ── statistics helpers ────────────────────────────────────────────────────

def basic_stats(results: list) -> Dict[str, object]:
    """Compute average/highest/lowest/pass_rate/excellent_rate from results.

    *results* must be a list of objects with ``.score`` and ``.percent``.
    """
    scores = [r.score for r in results]
    if not scores:
        return {"average": 0, "highest": 0, "lowest": 0,
                "pass_rate": 0, "excellent_rate": 0}
    return {
        "average": round(statistics.mean(scores), 2),
        "highest": round(max(scores), 2),
        "lowest": round(min(scores), 2),
        "pass_rate": round(
            sum(1 for r in results if r.percent >= 60)
            / len(results) * 100, 2),
        "excellent_rate": round(
            sum(1 for r in results if r.percent >= 90)
            / len(results) * 100, 2),
    }


def score_bands(results: list) -> List[Tuple[str, int]]:
    """Return count of students in each score band."""
    bands = [
        ("90%-100%", lambda p: p >= 90),
        ("80%-89%", lambda p: 80 <= p < 90),
        ("70%-79%", lambda p: 70 <= p < 80),
        ("60%-69%", lambda p: 60 <= p < 70),
        ("60%以下", lambda p: p < 60),
    ]
    return [(label, sum(1 for r in results if pred(r.percent)))
            for label, pred in bands]


# ── build_* analysis helpers (used by dashboard) ─────────────────────────

def build_score_distribution(results: list) -> List[Dict[str, object]]:
    return [
        {"label": label, "value": count,
         "class": "danger" if label == "60%以下" else "normal"}
        for label, count in score_bands(results)
    ]


def build_question_accuracy_items(
    item_analysis_rows: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    items = []
    for row in item_analysis_rows:
        accuracy = float(row.get("accuracy", 0))
        items.append({
            "label": f"Q{row.get('question')}",
            "value": accuracy,
            "display": percent(accuracy),
            "class": get_rate_class(accuracy),
        })
    return items


def main_wrong_answer(row: Dict[str, object]) -> str:
    distribution = row.get("distribution", {})
    if not isinstance(distribution, dict):
        return ""
    answer = str(row.get("answer", ""))
    candidates = []
    for option, count in distribution.items():
        option_text = str(option)
        if option_text in {"(blank)", "", answer}:
            continue
        candidates.append((option_text, int(count)))
    if not candidates:
        return ""
    option, count = max(candidates, key=lambda item: item[1])
    return f"{option}（{count}人）"


def build_weak_items(
    item_analysis_rows: List[Dict[str, object]], top_n: int = 5,
) -> List[Dict[str, object]]:
    sorted_rows = sorted(
        item_analysis_rows,
        key=lambda row: (float(row.get("accuracy", 0)),
                         int(row.get("question", 0))))
    items = []
    for row in sorted_rows[:top_n]:
        accuracy = float(row.get("accuracy", 0))
        if accuracy < 40:
            level = "重点讲评"
        elif accuracy < 60:
            level = "课堂订正"
        else:
            level = "适当回顾"
        items.append({
            "question": row.get("question", ""),
            "accuracy": accuracy,
            "blank_rate": float(row.get("blank_rate", 0)),
            "main_wrong": main_wrong_answer(row) or "暂无明显集中错误",
            "level": level,
            "class": get_rate_class(accuracy),
        })
    return items


def build_weak_tags(
    profiles: list, top_n: int = 10,
) -> List[Dict[str, object]]:
    """profiles must be a list of objects with ``.tag`` and ``.mastery``."""
    tag_profiles: Dict[str, list] = defaultdict(list)
    for p in profiles:
        tag_profiles[p.tag].append(p)
    rows = []
    for tag, items in tag_profiles.items():
        mastery = round(statistics.mean(i.mastery for i in items), 2)
        rows.append({
            "label": tag, "value": mastery,
            "display": percent(mastery),
            "class": get_rate_class(mastery),
        })
    return sorted(rows, key=lambda r: (float(r["value"]), str(r["label"])))[
        :top_n
    ]


def build_abnormal_items(
    item_analysis_rows: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    items = []
    for row in item_analysis_rows:
        badges = []
        blank_rate = float(row.get("blank_rate", 0))
        invalid_rate = float(row.get("invalid_rate", 0))
        partial_rate = float(row.get("partial_rate", 0))
        if blank_rate >= 20:
            badges.append(("空白较多", "badge-warning"))
        if invalid_rate >= 10:
            badges.append(("作答异常", "badge-danger"))
        if partial_rate >= 20:
            badges.append(("漏选较多", "badge-warning"))
        if badges:
            items.append({
                "question": row.get("question", ""),
                "blank_rate": blank_rate,
                "invalid_rate": invalid_rate,
                "partial_rate": partial_rate,
                "badges": badges,
            })
    return items


def build_teaching_suggestions(
    item_analysis_rows: List[Dict[str, object]],
    profiles: list,
) -> List[Dict[str, str]]:
    suggestions: List[Dict[str, str]] = []
    for row in item_analysis_rows:
        question = row.get("question", "")
        accuracy = float(row.get("accuracy", 0))
        blank_rate = float(row.get("blank_rate", 0))
        invalid_rate = float(row.get("invalid_rate", 0))
        partial_rate = float(row.get("partial_rate", 0))
        if accuracy < 40:
            suggestions.append({
                "badge": "重点讲评", "class": "badge-danger",
                "text": f"第 {question} 题正确率较低，建议重点讲评。"})
        elif accuracy < 60:
            suggestions.append({
                "badge": "课堂订正", "class": "badge-warning",
                "text": f"第 {question} 题正确率中等偏低，建议课堂订正。"})
        if blank_rate >= 20:
            suggestions.append({
                "badge": "时间/难度", "class": "badge-warning",
                "text": f"第 {question} 题空白率较高，可能存在时间不足或题目难度偏高。"})
        if partial_rate >= 20:
            suggestions.append({
                "badge": "漏选问题", "class": "badge-warning",
                "text": f"第 {question} 题部分得分较多，可能存在漏选或理解不完整。"})
        if invalid_rate >= 10:
            suggestions.append({
                "badge": "作答异常", "class": "badge-danger",
                "text": f"第 {question} 题作答格式异常较多，建议检查答题卡或识别结果。"})

    weak_tags = build_weak_tags(profiles, top_n=10)
    for row in weak_tags:
        if float(row["value"]) < 60:
            suggestions.append({
                "badge": "知识点薄弱", "class": "badge-info",
                "text": f"知识点【{row['label']}】平均掌握率较低，建议后续针对性巩固。"})
    return suggestions[:18]


# ── HTML rendering helpers ────────────────────────────────────────────────

def render_table(headers: List[str], rows: List[List[object]]) -> str:
    header_html = "".join(
        f"<th>{html_escape(h)}</th>" for h in headers)
    row_html = []
    for row in rows:
        row_html.append(
            "<tr>" + "".join(
                f"<td>{html_escape(cell)}</td>" for cell in row
            ) + "</tr>")
    return (
        f"<table><thead><tr>{header_html}</tr></thead>"
        f"<tbody>{''.join(row_html)}</tbody></table>"
    )


def bar(label: str, value: float, max_value: float = 100.0) -> str:
    width = 0 if max_value <= 0 else min(100, max(0, value / max_value * 100))
    return (
        '<div class="bar-row">'
        f'<span>{html_escape(label)}</span>'
        f'<div class="bar-track"><div class="bar-fill" '
        f'style="width:{width:.2f}%"></div></div>'
        f'<strong>{html_escape(value)}</strong>'
        '</div>'
    )


def report_link(path: Any, label: str, css_class: str) -> str:
    """Conditional link: if path exists render <a>, else disabled <div>."""
    from pathlib import Path as _Path
    p = _Path(str(path)) if not isinstance(path, _Path) else path
    if p.exists():
        return (
            f'<a class="btn {css_class}" href="{html_escape(p.name)}">'
            f'{html_escape(label)}</a>'
        )
    return (
        f'<div class="btn {css_class} disabled">'
        f'{html_escape(label)}<span>文件暂未生成</span></div>'
    )


def render_metric_cards(metrics: List[Dict[str, object]]) -> str:
    return '<section class="metric-grid">' + "".join(
        f'<div class="metric-card">'
        f'<div class="label">{html_escape(m["label"])}</div>'
        f'<div class="value">{html_escape(m["value"])}</div>'
        f'<div class="hint">{html_escape(m["hint"])}</div>'
        f'</div>'
        for m in metrics
    ) + "</section>"


def render_vertical_bar_chart(
    title: str, items: List[Dict[str, object]], description: str = "",
) -> str:
    if not items:
        return '<div class="empty">暂无数据</div>'
    max_value = max(float(i.get("value", 0)) for i in items) or 1
    bars = []
    for item in items:
        value = float(item.get("value", 0))
        height = max(3, value / max_value * 170)
        css_class = item.get("class", "normal")
        display = item.get("display", str(item.get("value", "")))
        bars.append(
            f'<div class="vbar">'
            f'<div class="vbar-value">{html_escape(display)}</div>'
            f'<div class="vbar-fill {html_escape(css_class)}" '
            f'style="height:{height:.2f}px"></div>'
            f'<div class="vbar-label">{html_escape(item.get("label", ""))}'
            f'</div></div>')
    return (
        f'<div class="vertical-scroll"><div class="vertical-chart">'
        f'{"".join(bars)}</div></div>'
    )


def render_horizontal_bar_chart(
    title: str, items: List[Dict[str, object]], description: str = "",
) -> str:
    if not items:
        return '<div class="empty">暂无数据</div>'
    rows = []
    for item in items:
        value = float(item.get("value", 0))
        rows.append(
            f'<div class="bar-row">'
            f'<div class="bar-label" title="{html_escape(item.get("label", ""))}">'
            f'{html_escape(item.get("label", ""))}</div>'
            f'<div class="bar-track"><div class="bar-fill '
            f'{html_escape(item.get("class", "normal"))}" '
            f'style="width:{max(0, min(100, value)):.2f}%"></div></div>'
            f'<div class="bar-value">'
            f'{html_escape(item.get("display", percent(value)))}</div></div>')
    return f'<div class="bar-chart">{"".join(rows)}</div>'


def render_wrong_top(items: List[Dict[str, object]]) -> str:
    if not items:
        return '<div class="empty">暂无题目分析数据</div>'
    cards = []
    for item in items:
        cards.append(
            f'<div class="wrong-item {html_escape(item["class"])}">'
            f'<div class="wrong-head">'
            f'<span>第 {html_escape(item["question"])} 题</span>'
            f'<span>{html_escape(item["level"])}</span></div>'
            f'<div class="wrong-meta">正确率 {percent(item["accuracy"])}'
            f' · 空白率 {percent(item["blank_rate"])}'
            f' · 主要错误答案：{html_escape(item["main_wrong"])}</div>'
            f'<div class="bar-track" style="margin-top:10px">'
            f'<div class="bar-fill {html_escape(item["class"])}" '
            f'style="width:{max(0, min(100, float(item["accuracy"]))):.2f}%">'
            f'</div></div></div>')
    return f'<div class="wrong-list">{"".join(cards)}</div>'


def render_abnormal_table(items: List[Dict[str, object]]) -> str:
    if not items:
        return '<div class="empty">本次考试未发现明显作答异常</div>'
    rows = []
    for item in items:
        badges = "".join(
            f'<span class="badge {html_escape(css)}">{html_escape(text)}</span>'
            for text, css in item["badges"])
        rows.append(
            f"<tr><td>Q{html_escape(item['question'])}</td>"
            f"<td>{percent(item['blank_rate'])}</td>"
            f"<td>{percent(item['invalid_rate'])}</td>"
            f"<td>{percent(item['partial_rate'])}</td>"
            f"<td>{badges}</td></tr>")
    return (
        '<table class="compact-table"><thead><tr>'
        '<th>题号</th><th>空白率</th><th>非法率</th>'
        '<th>部分得分率</th><th>提醒</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table>'
    )


def render_suggestion_cards(suggestions: List[Dict[str, str]]) -> str:
    if not suggestions:
        return '<div class="empty">暂无需要特别讲评的建议</div>'
    return '<div class="suggestions">' + "".join(
        f'<div class="suggestion-card">'
        f'<span class="badge {html_escape(s["class"])}">'
        f'{html_escape(s["badge"])}</span>'
        f'<p>{html_escape(s["text"])}</p></div>'
        for s in suggestions
    ) + "</div>"


def render_option_distribution(item_rows: List[Dict[str, object]]) -> str:
    if not item_rows:
        return '<div class="empty">暂无题目分析数据</div>'
    cards = []
    for row in item_rows:
        distribution = row.get("distribution", {})
        if not isinstance(distribution, dict):
            distribution = {}
        lines = "".join(
            f'<div class="bar-row" '
            f'style="grid-template-columns:60px 1fr 44px">'
            f'<div class="bar-label">{html_escape(opt)}</div>'
            f'<div class="bar-track"><div class="bar-fill normal" '
            f'style="width:{min(100, int(cnt) * 20):.2f}%"></div></div>'
            f'<div class="bar-value">{html_escape(cnt)}</div></div>'
            for opt, cnt in sorted(distribution.items()))
        body = lines or '<div class="empty">暂无数据</div>'
        cards.append(
            f'<div class="option-card">'
            f'<h3>Q{html_escape(row.get("question", ""))}</h3>'
            f'{body}</div>')
    return f'<div class="option-grid">{"".join(cards)}</div>'


# ── CSS blocks (verbatim from legacy) ─────────────────────────────────────

def report_css() -> str:
    return """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;margin:0;background:#f6f7f9;color:#20242a}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:28px;margin:0 0 8px} h2{font-size:18px;margin:28px 0 12px}
.muted{color:#667085}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stat,.panel{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px}
.stat b{display:block;font-size:24px;margin-top:6px}.actions{margin:18px 0}
a.button{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;padding:10px 14px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}
th,td{border-bottom:1px solid #edf0f3;padding:8px 10px;text-align:left;font-size:14px}th{background:#f1f5f9}
.bar-row{display:grid;grid-template-columns:90px 1fr 64px;gap:10px;align-items:center;margin:8px 0}
.bar-track{height:14px;background:#e5e7eb;border-radius:999px;overflow:hidden}.bar-fill{height:100%;background:#2563eb}
.warn{background:#fff7ed;border-color:#fed7aa}.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){main{padding:16px}.two{grid-template-columns:1fr}th,td{font-size:12px;padding:6px}.bar-row{grid-template-columns:70px 1fr 52px}}
"""


def advanced_dashboard_css() -> str:
    return """
:root{--bg:#f5f7fb;--card:#fff;--line:#e6eaf2;--text:#1f2937;--muted:#667085;--blue:#2f6fed;--green:#16a34a;--orange:#f59e0b;--red:#ef4444;--shadow:0 10px 26px rgba(31,41,55,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.55}
.report-shell{max-width:1200px;margin:0 auto;padding:28px}.report-header{background:linear-gradient(135deg,#fff,#eef5ff);border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:var(--shadow);margin-bottom:18px}
.report-header h1{margin:0 0 10px;font-size:30px}.meta-line{display:flex;flex-wrap:wrap;gap:10px 18px;color:var(--muted)}
.metric-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:18px 0}.metric-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow)}
.metric-card .label{color:var(--muted);font-size:14px}.metric-card .value{font-size:28px;font-weight:750;margin:4px 0}.metric-card .hint{color:var(--muted);font-size:13px}
.dashboard-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.chart-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow);min-width:0}
.chart-card.wide{grid-column:1/-1}.chart-card h2{font-size:19px;margin:0 0 6px}.chart-desc{color:var(--muted);margin:0 0 16px}.empty{color:var(--muted);background:#f8fafc;border:1px dashed #cbd5e1;border-radius:12px;padding:18px;text-align:center}
.vertical-scroll{overflow-x:auto;padding-top:16px}.vertical-chart{display:flex;align-items:flex-end;gap:14px;min-height:230px;min-width:max-content;border-left:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px 12px 10px}
.vbar{width:72px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;min-height:190px}.vbar-value{font-weight:700;margin-bottom:6px}.vbar-fill{width:42px;border-radius:10px 10px 4px 4px;background:var(--blue);min-height:4px}.vbar-fill.danger{background:var(--red)}.vbar-fill.warning{background:var(--orange)}.vbar-fill.normal{background:var(--blue)}.vbar-fill.good{background:var(--green)}.vbar-label{margin-top:8px;color:var(--muted);font-size:13px;text-align:center;white-space:nowrap}
.bar-chart{display:flex;flex-direction:column;gap:12px}.bar-row{display:grid;grid-template-columns:minmax(92px,160px) 1fr 74px;gap:12px;align-items:center}.bar-label{font-weight:650;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{height:16px;background:#edf2f7;border-radius:999px;overflow:hidden}.bar-fill{height:100%;background:var(--blue);border-radius:999px}.bar-fill.danger{background:var(--red)}.bar-fill.warning{background:var(--orange)}.bar-fill.normal{background:var(--blue)}.bar-fill.good{background:var(--green)}.bar-value{text-align:right;font-weight:700}
.wrong-list{display:flex;flex-direction:column;gap:12px}.wrong-item{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fbfdff}.wrong-head{display:flex;justify-content:space-between;gap:12px;font-weight:750}.wrong-item.danger{border-color:#fecaca;background:#fff7f7}.wrong-item.warning{border-color:#fed7aa;background:#fffaf2}.wrong-meta{color:var(--muted);font-size:14px;margin-top:6px}
.compact-table{width:100%;border-collapse:collapse}.compact-table th,.compact-table td{border-bottom:1px solid var(--line);padding:9px;text-align:left}.compact-table th{color:var(--muted);font-weight:700;background:#f8fafc}.badge{display:inline-block;border-radius:999px;padding:4px 9px;font-size:12px;font-weight:700;margin:2px;background:#e0ecff;color:#1d4ed8}.badge-danger{background:#fee2e2;color:#b91c1c}.badge-warning{background:#fef3c7;color:#a16207}.badge-info{background:#dbeafe;color:#1d4ed8}.badge-good{background:#dcfce7;color:#166534}
.suggestions{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.suggestion-card{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fff}.suggestion-card p{margin:8px 0 0}
.option-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.option-card{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fbfdff}.option-card h3{margin:0 0 8px;font-size:15px}
@media(max-width:980px){.metric-grid{grid-template-columns:repeat(3,1fr)}.dashboard-grid{grid-template-columns:1fr}.suggestions{grid-template-columns:1fr}}
@media(max-width:640px){.report-shell{padding:16px}.metric-grid{grid-template-columns:1fr 1fr}.bar-row{grid-template-columns:80px 1fr 58px}.metric-card .value{font-size:24px}.report-header h1{font-size:24px}}
@media print{body{background:#fff}.report-shell{max-width:none;padding:0}.report-header,.metric-card,.chart-card{box-shadow:none;break-inside:avoid}.chart-card{page-break-inside:avoid}.dashboard-grid{grid-template-columns:1fr}.bar-fill,.vbar-fill{background:#555!important}.badge{border:1px solid #999;background:#fff!important;color:#111!important}}
"""


# ── index CSS (inline, not a function in legacy) ──────────────────────────

def index_css() -> str:
    return """
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;background:#f5f7fb;color:#172033}
.shell{max-width:820px;margin:60px auto;padding:32px}
.card{background:#fff;border-radius:18px;padding:32px;box-shadow:0 16px 40px rgba(15,23,42,.08)}
h1{margin:0 0 10px;font-size:30px}
.meta{color:#667085;margin-bottom:28px;line-height:1.8;font-size:16px}
.actions{display:grid;gap:16px}
.btn{display:block;padding:18px 22px;border-radius:14px;text-decoration:none;font-size:18px;font-weight:700}
.btn span{display:block;margin-top:5px;font-size:14px;font-weight:500}
.btn-primary{background:#2563eb;color:white}
.btn-success{background:#16a34a;color:white}
.btn-outline{background:white;color:#172033;border:1px solid #d8dee8}
.disabled{background:#eef2f7;color:#667085;border:1px solid #d8dee8;cursor:not-allowed}
.hint{margin-top:24px;color:#667085;font-size:14px;line-height:1.7}
@media (max-width:640px){.shell{margin:20px auto;padding:16px}.card{padding:24px}h1{font-size:26px}.btn{font-size:17px}}
"""
