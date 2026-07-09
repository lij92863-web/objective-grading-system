"""ReportIndexHtmlExporter — generates ``index.html``.

Matches ``legacy.write_report_index`` in structure, links, CSS.
Does NOT import legacy or web.
"""

from pathlib import Path
from typing import Any, Dict

from .contracts import ExportRequest, ExportResult
from .html_helpers import html_escape, index_css, report_link

OUTPUT_FILENAME = "index.html"


class ReportIndexHtmlExporter:
    """Export the report index / landing page HTML."""

    def export(
        self,
        request: ExportRequest,
        meta: Dict[str, str],
        simple_report_path: Any = None,
        advanced_dashboard_path: Any = None,
        simple_score_report_path: Any = None,
    ) -> ExportResult:
        """Write ``index.html``.

        Parameters
        ----------
        request: ExportRequest
        meta: dict with exam_name, class_name, subject, exam_date
        simple_report_path: path-like to simple_report.html
        advanced_dashboard_path: path-like to advanced_dashboard.html
        simple_score_report_path: path-like to simple_score_report.xlsx
        """
        out_dir = Path(request.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Resolve paths relative to output_dir if not absolute
        def _resolve(p):
            if p is None:
                return None
            p = Path(str(p))
            if not p.is_absolute():
                p = out_dir / p
            return p

        srp = _resolve(simple_report_path) or (out_dir / "simple_report.html")
        adp = _resolve(advanced_dashboard_path) or (
            out_dir / "advanced_dashboard.html")
        ssp = _resolve(simple_score_report_path) or (
            out_dir / "simple_score_report.xlsx")

        exam_name = str(meta.get("exam_name", "未填写"))
        class_name = str(meta.get("class_name", "未填写"))
        subject = str(meta.get("subject", "未填写"))
        exam_date = str(meta.get("exam_date", "未填写"))

        html = (
            '<!DOCTYPE html>\n'
            f'<html lang="zh-CN">\n'
            f'<head>\n'
            f'<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>批改完成</title>\n'
            f'<style>{index_css()}</style>\n'
            f'</head>\n'
            f'<body>\n'
            f'<div class="shell">\n'
            f'  <div class="card">\n'
            f'    <h1>本次批改完成</h1>\n'
            f'    <div class="meta">\n'
            f'      考试：{html_escape(exam_name)}<br>\n'
            f'      班级：{html_escape(class_name)}<br>\n'
            f'      科目：{html_escape(subject)}<br>\n'
            f'      日期：{html_escape(exam_date)}\n'
            f'    </div>\n'
            f'    <div class="actions">\n'
            f'      {report_link(srp, "查看普通版报告", "btn-primary")}\n'
            f'      {report_link(adp, "查看高级学情分析", "btn-success")}\n'
            f'      {report_link(ssp, "打开简单成绩表", "btn-outline")}\n'
            f'    </div>\n'
            f'    <div class="hint">普通老师建议先查看"普通版报告"。'
            f'需要深入分析时，再打开"高级学情分析"。</div>\n'
            f'  </div>\n'
            f'</div>\n'
            f'</body>\n'
            f'</html>\n'
        )

        output_path = out_dir / OUTPUT_FILENAME
        output_path.write_text(html, encoding="utf-8")

        return ExportResult(
            status="ok",
            generated_files=(str(output_path),),
            source="report_index_html_exporter",
        )
