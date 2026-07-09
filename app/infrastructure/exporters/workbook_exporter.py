"""WorkbookExporter — generates ``exam_report.xlsx`` (9 sheets).

Matches the behaviour of ``legacy.write_workbook``: reads CSV files
via ``csv.reader``, writes an xlsx with one sheet per CSV.

Does NOT import legacy, web, openpyxl, xlsxwriter, or pandas.
Does NOT recompute data — only reads existing CSVs.
"""

import csv
from pathlib import Path
from typing import Any, List, Tuple

from .contracts import ExportRequest, ExportResult
from .xlsx_helpers import XlsxSheet, write_xlsx

# Must match legacy write_workbook sheet order and names exactly.
# Order is significant — sheets appear in the workbook in this order.
EXPECTED_SHEETS: List[Tuple[str, str]] = [
    ("成绩总表", "summary.csv"),
    ("每题明细", "detail.csv"),
    ("每题分析", "item_analysis.csv"),
    ("知识点画像", "knowledge_profile.csv"),
    ("学生错题", "student_wrong_list.csv"),
    ("讲评计划", "teaching_plan.csv"),
    ("班级补救", "class_remedial_package.csv"),
    ("分层补救", "layered_remedial_plan.csv"),
    ("数据质量检查", "validation_report.csv"),
]

OUTPUT_FILENAME = "exam_report.xlsx"


class WorkbookExporter:
    """Export a full workbook (9 sheets) from existing CSV files."""

    def export(
        self,
        request: ExportRequest,
        data: List[Tuple[str, Path]],
    ) -> ExportResult:
        """Write ``exam_report.xlsx``.

        Parameters
        ----------
        request:
            Export request carrying at minimum ``output_dir``.
        data:
            Ordered list of ``(sheet_name, csv_path)`` tuples.
            Each CSV file must exist and be UTF-8-BOM encoded.
            Sheet order is preserved in the output workbook.

        Returns
        -------
        ExportResult:
            Result with ``generated_files`` containing the xlsx path.
        """
        out_dir = Path(request.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        sheets: List[XlsxSheet] = []
        for sheet_name, csv_path in data:
            csv_p = Path(csv_path)
            rows: List[List[str]] = []
            if csv_p.exists():
                with csv_p.open("r", encoding="utf-8-sig", newline="") as handle:
                    rows = [list(row) for row in csv.reader(handle)]
            if not rows:
                rows = [["empty"]]
            sheets.append(XlsxSheet(name=sheet_name, rows=rows))

        output_path = out_dir / OUTPUT_FILENAME
        write_xlsx(output_path, sheets)

        return ExportResult(
            status="ok",
            generated_files=(str(output_path),),
            source="workbook_exporter",
        )
