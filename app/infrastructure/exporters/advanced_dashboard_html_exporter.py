"""AdvancedDashboardHtmlExporter — generates ``advanced_dashboard.html``.

Matches ``legacy.write_advanced_dashboard`` in structure, titles, CSS, charts.
Does NOT import legacy or web.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .contracts import ExportRequest, ExportResult
from .html_helpers import (
    advanced_dashboard_css,
    basic_stats,
    build_abnormal_items,
    build_question_accuracy_items,
    build_score_distribution,
    build_teaching_suggestions,
    build_weak_items,
    build_weak_tags,
    html_escape,
    render_abnormal_table,
    render_horizontal_bar_chart,
    render_metric_cards,
    render_option_distribution,
    render_suggestion_cards,
    render_table,
    render_vertical_bar_chart,
    render_wrong_top,
)

OUTPUT_FILENAME = "advanced_dashboard.html"


class AdvancedDashboardHtmlExporter:
    """Export the advanced analytics dashboard HTML report."""

    def export(
        self,
        request: ExportRequest,
        meta: Dict[str, str],
        results: List[Any],
        profiles: List[Any],
        validation_rows: List[Dict[str, Any]],
        item_rows: List[Dict[str, Any]],
    ) -> ExportResult:
        """Write ``advanced_dashboard.html``.

        Parameters
        ----------
        request: ExportRequest
        meta: dict with exam_name, class_name, subject, exam_date
        results: list of StudentResult
        profiles: list of KnowledgeProfile
        validation_rows: list of dicts (severity, scope, item, message)
        item_rows: list of dicts from item_analysis
        """
        out_dir = Path(request.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        stats = basic_stats(results)
        metrics = [
            {"label": "参考人数", "value": len(results),
             "hint": "参与本次批改的学生数"},
            {"label": "平均分", "value": stats["average"],
             "hint": "班级总体水平"},
            {"label": "最高分", "value": stats["highest"],
             "hint": "本次最高成绩"},
            {"label": "最低分", "value": stats["lowest"],
             "hint": "需重点关注"},
            {"label": "及格率", "value": f"{stats['pass_rate']:.2f}%",
             "hint": "60% 及以上"},
            {"label": "优秀率", "value": f"{stats['excellent_rate']:.2f}%",
             "hint": "90% 及以上"},
        ]

        score_dist = build_score_distribution(results)
        accuracy_items = build_question_accuracy_items(item_rows)
        weak_items = build_weak_items(item_rows)
        weak_tags = build_weak_tags(profiles)
        abnormal_items = build_abnormal_items(item_rows)
        suggestions = build_teaching_suggestions(item_rows, profiles)

        warning_rows = [r for r in validation_rows
                        if r.get("severity") in {"warning", "error"}]
        warning_html = (
            render_table(
                ["级别", "范围", "项目", "提醒"],
                [[r.get("severity", ""), r.get("scope", ""),
                  r.get("item", ""), r.get("message", "")]
                 for r in warning_rows],
            ) if warning_rows
            else '<div class="empty">暂无未匹配、低置信度或异常答案提醒</div>'
        )
        weak_tag_body = (
            render_horizontal_bar_chart("班级薄弱知识点", weak_tags)
            if weak_tags
            else '<div class="empty">暂无知识点数据</div>'
        )
        generated_at = datetime.now().replace(microsecond=0).strftime(
            "%Y-%m-%d %H:%M:%S")

        exam_name = str(meta.get("exam_name", ""))
        class_name = str(meta.get("class_name", "") or "未填写")
        subject = str(meta.get("subject", "") or "未填写")
        exam_date = str(meta.get("exam_date", ""))

        html = (
            '<!doctype html>\n'
            f'<html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>高级学情分析报告 - {html_escape(exam_name)}</title>'
            f'<style>{advanced_dashboard_css()}</style></head>\n'
            f'<body><main class="report-shell">\n'
            f'<header class="report-header">'
            f'<h1>高级学情分析报告</h1>'
            f'<div class="meta-line">'
            f'<span>考试名称：{html_escape(exam_name)}</span>'
            f'<span>班级：{html_escape(class_name)}</span>'
            f'<span>科目：{html_escape(subject)}</span>'
            f'<span>考试日期：{html_escape(exam_date)}</span>'
            f'<span>生成时间：{html_escape(generated_at)}</span>'
            f'</div></header>\n'
            f'{render_metric_cards(metrics)}\n'
            f'<section class="dashboard-grid">\n'
            f'<article class="chart-card">'
            f'<h2>成绩分布</h2>'
            f'<p class="chart-desc">查看班级成绩集中区间。</p>'
            f'{render_vertical_bar_chart("成绩分布", score_dist)}'
            f'</article>\n'
            f'<article class="chart-card">'
            f'<h2>每题正确率</h2>'
            f'<p class="chart-desc">低于 40% 标红，40%-60% 标橙。</p>'
            f'{render_vertical_bar_chart("每题正确率", accuracy_items)}'
            f'</article>\n'
            f'<article class="chart-card">'
            f'<h2>易错题 Top 5</h2>'
            f'<p class="chart-desc">按正确率从低到高排序。</p>'
            f'{render_wrong_top(weak_items)}'
            f'</article>\n'
            f'<article class="chart-card">'
            f'<h2>班级薄弱知识点</h2>'
            f'<p class="chart-desc">按全班平均掌握率从低到高展示 Top 10。</p>'
            f'{weak_tag_body}'
            f'</article>\n'
            f'<article class="chart-card">'
            f'<h2>答题异常情况</h2>'
            f'<p class="chart-desc">空白、非法答案、漏选较多的题会被标记。</p>'
            f'{render_abnormal_table(abnormal_items)}'
            f'</article>\n'
            f'<article class="chart-card">'
            f'<h2>教学讲评建议</h2>'
            f'<p class="chart-desc">把题目与知识点数据转换成可执行建议。</p>'
            f'{render_suggestion_cards(suggestions)}'
            f'</article>\n'
            f'<article class="chart-card wide">'
            f'<h2>每题选项分布</h2>'
            f'<p class="chart-desc">用于观察学生主要误选项或空白集中情况。</p>'
            f'{render_option_distribution(item_rows)}'
            f'</article>\n'
            f'<article class="chart-card wide">'
            f'<h2>未匹配、低置信度、异常答案等提醒</h2>'
            f'{warning_html}'
            f'</article>\n'
            f'</section>\n'
            f'</main></body></html>'
        )

        output_path = out_dir / OUTPUT_FILENAME
        output_path.write_text(html, encoding="utf-8")

        return ExportResult(
            status="ok",
            generated_files=(str(output_path),),
            source="advanced_dashboard_html_exporter",
        )
