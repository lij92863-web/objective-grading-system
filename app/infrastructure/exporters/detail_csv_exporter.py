"""Detail CSV exporter — matches legacy ``write_detail`` output.

Does NOT import legacy, web, or any grading/recognition module.
Only writes pre-computed detail rows to CSV.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

# Must match legacy write_detail field order exactly.
DETAIL_FIELDNAMES = [
    "student_id",
    "name",
    "question",
    "question_id",
    "question_status",
    "difficulty",
    "tags",
    "expected",
    "actual",
    "raw_actual",
    "score",
    "max_score",
    "status",
]


class DetailCsvExporter(ReportExporter):
    """Export a ``detail.csv`` file from pre-computed detail rows.

    Usage::

        exporter = DetailCsvExporter()
        result = exporter.export(
            ExportRequest(output_dir=Path("./out")),
            rows,   # list of dicts with DETAIL_FIELDNAMES keys
        )
    """

    def export(
        self,
        request: ExportRequest,
        data: object,
        fieldnames: Optional[List[str]] = None,
    ) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(DETAIL_FIELDNAMES)

        rows: List[Dict[str, object]] = []
        if isinstance(data, list):
            rows = data

        if not rows:
            out_path = request.output_dir / "detail.csv"
            write_dict_rows_csv(out_path, [], fieldnames=fieldnames)
            return ExportResult(
                status="ok",
                generated_files=("detail.csv",),
                warnings=("detail_rows_empty",),
                source="detail_csv_exporter",
            )

        out_path = request.output_dir / "detail.csv"
        write_dict_rows_csv(out_path, rows, fieldnames=fieldnames)
        return ExportResult(
            status="ok",
            generated_files=("detail.csv",),
            source="detail_csv_exporter",
        )
