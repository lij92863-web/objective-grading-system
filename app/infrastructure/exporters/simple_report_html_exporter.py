"""SimpleReportHtmlExporter — generates ``simple_report.html``.

Matches ``legacy.write_simple_report`` in structure, titles, CSS, links.
Does NOT import legacy or web.
"""

from pathlib import Path
from typing import Any, Dict, List

from .contracts import ExportRequest, ExportResult
from .html_helpers import (
    bar,
    basic_stats,
    html_escape,
    pct,
    render_table,
    report_css,
)

OUTPUT_FILENAME = "simple_report.html"


class SimpleReportHtmlExporter:
    """Export the simple (teacher-facing) HTML report."""

    def export(
        self,
        request: ExportRequest,
        meta: Dict[str, str],
        results: List[Any],
        simple_rows: List[Dict[str, Any]],
        item_rows: List[Dict[str, Any]],
    ) -> ExportResult:
        """Write ``simple_report.html``.

        Parameters
        ----------
        request: ExportRequest
        meta: dict with keys exam_name, class_name, exam_date, subject
        results: list of StudentResult (for basic_stats)
        simple_rows: list of dicts from simple_score_rows
        item_rows: list of dicts from item_stats
        """
        out_dir = Path(request.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        stats = basic_stats(results)
        top_wrong = sorted(
            item_rows,
            key=lambda r: (-float(r["mistake_count"]), r["question"]),
        )[:5]

        score_table = render_table(
            ["rank", "student_id", "name", "score", "max_score",
             "percent", "correct_count", "wrong_or_partial_count",
             "blank_count", "wrong_questions"],
            [
                [r["rank"], r["student_id"], r["name"], r["score"],
                 r["max_score"], r["percent"], r["correct_count"],
                 r["wrong_or_partial_count"], r["blank_count"],
                 r["wrong_questions"]]
                for r in simple_rows
            ],
        )
        item_table = render_table(
            ["题号", "正确率", "空白率"],
            [[f"Q{r['question']}", pct(float(r["accuracy"])),
              pct(float(r["blank_rate"]))] for r in item_rows],
        )
        top_table = render_table(
            ["题号", "错误/部分得分人数", "正确率", "知识点"],
            [[f"Q{r['question']}", r["mistake_count"],
              pct(float(r["accuracy"])), r["tags"]] for r in top_wrong],
        )
        bars = "".join(
            bar(f"Q{r['question']}", float(r["accuracy"]))
            for r in item_rows)

        exam_name = str(meta.get("exam_name", ""))
        class_name = str(meta.get("class_name", "") or "未填写班级")
        exam_date = str(meta.get("exam_date", ""))

        html = (
            '<!doctype html>\n'
            f'<html lang="zh-CN"><head><meta charset="utf-8">'
            f'<title>普通版报告 - {html_escape(exam_name)}</title>'
            f'<style>{report_css()}</style></head>\n'
            f'<body><main>\n'
            f'<h1>普通版报告</h1>'
            f'<p class="muted">{html_escape(exam_name)}'
            f' · {html_escape(class_name)}'
            f' · {html_escape(exam_date)}</p>\n'
            f'<div class="actions">'
            f'<a class="button" href="simple_score_report.xlsx">'
            f'导出简单 Excel 成绩表</a></div>\n'
            f'<section class="grid">\n'
            f'<div class="stat">参考人数<b>{len(results)}</b></div>\n'
            f'<div class="stat">平均分<b>{stats["average"]}</b></div>\n'
            f'<div class="stat">最高分<b>{stats["highest"]}</b></div>\n'
            f'<div class="stat">最低分<b>{stats["lowest"]}</b></div>\n'
            f'<div class="stat">及格率<b>{pct(float(stats["pass_rate"]))}</b></div>\n'
            f'<div class="stat">优秀率<b>{pct(float(stats["excellent_rate"]))}</b></div>\n'
            f'</section>\n'
            f'<h2>学生成绩表</h2>{score_table}\n'
            f'<section class="two"><div><h2>每题正确率</h2>'
            f'<div class="panel">{bars}</div></div>'
            f'<div><h2>每题正确率表</h2>{item_table}</div></section>\n'
            f'<h2>错得最多的题 Top 5</h2>{top_table}\n'
            f'</main></body></html>'
        )

        output_path = out_dir / OUTPUT_FILENAME
        output_path.write_text(html, encoding="utf-8")

        return ExportResult(
            status="ok",
            generated_files=(str(output_path),),
            source="simple_report_html_exporter",
        )
