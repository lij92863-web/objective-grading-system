"""SimpleScoreWorkbookExporter — generates ``simple_score_report.xlsx``.

Matches the behaviour of ``legacy.write_simple_score_workbook``:
same filename, same sheet name, same fields, same inlineStr approach.

Does NOT import legacy, web, openpyxl, xlsxwriter, or pandas.
Does NOT recompute scores — receives a pre-built dict list.
"""

from pathlib import Path
from typing import Any, Dict, List

from .contracts import ExportRequest, ExportResult
from .xlsx_helpers import XlsxSheet, write_xlsx

# Must match legacy.write_simple_score_workbook field order exactly
FIELDS = [
    "rank",
    "student_id",
    "name",
    "score",
    "max_score",
    "percent",
    "correct_count",
    "wrong_or_partial_count",
    "blank_count",
    "invalid_count",
    "wrong_questions",
    "blank_questions",
    "remark",
]

OUTPUT_FILENAME = "simple_score_report.xlsx"
SHEET_NAME = "scores"


class SimpleScoreWorkbookExporter:
    """Export a simple score workbook from pre-computed score rows."""

    def export(
        self,
        request: ExportRequest,
        data: List[Dict[str, Any]],
    ) -> ExportResult:
        """Write ``simple_score_report.xlsx``.

        Parameters
        ----------
        request:
            Export request carrying at minimum ``output_dir``.
        data:
            List of dicts in the format produced by ``simple_score_rows``.
            Each dict must contain the keys defined in ``FIELDS``.

        Returns
        -------
        ExportResult:
            Result with ``generated_files`` containing the xlsx path.
        """
        out_dir = Path(request.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Build rows: header row + one row per student
        rows: List[List[Any]] = [list(FIELDS)]
        for row in data:
            rows.append([str(row.get(field, "")) for field in FIELDS])

        output_path = out_dir / OUTPUT_FILENAME
        write_xlsx(output_path, [XlsxSheet(name=SHEET_NAME, rows=rows)])

        return ExportResult(
            status="ok",
            generated_files=(str(output_path),),
            source="simple_score_workbook_exporter",
        )
