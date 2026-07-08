"""Summary CSV exporter — matches legacy ``write_summary`` output.

Does NOT import legacy, web, or any grading/recognition module.
Only writes pre-computed summary rows to CSV.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

# Must match legacy write_summary field order exactly.
SUMMARY_FIELDNAMES = [
    "student_id",
    "name",
    "rank",
    "score",
    "max_score",
    "percent",
    "correct_count",
    "wrong_or_partial_count",
    "blank_count",
    "invalid_count",
]


class SummaryCsvExporter(ReportExporter):
    """Export a ``summary.csv`` file from pre-computed summary rows.

    Usage::

        exporter = SummaryCsvExporter()
        result = exporter.export(
            ExportRequest(output_dir=Path("./out")),
            rows,   # list of dicts with SUMMARY_FIELDNAMES keys
        )
    """

    def export(
        self,
        request: ExportRequest,
        data: object,
        fieldnames: Optional[List[str]] = None,
    ) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(SUMMARY_FIELDNAMES)

        rows: List[Dict[str, object]] = []
        if isinstance(data, list):
            rows = data

        if not rows:
            # Write header-only file — not a hard error, but flag it
            out_path = request.output_dir / "summary.csv"
            write_dict_rows_csv(out_path, [], fieldnames=fieldnames)
            return ExportResult(
                status="ok",
                generated_files=("summary.csv",),
                warnings=("summary_rows_empty",),
                source="summary_csv_exporter",
            )

        out_path = request.output_dir / "summary.csv"
        write_dict_rows_csv(out_path, rows, fieldnames=fieldnames)
        return ExportResult(
            status="ok",
            generated_files=("summary.csv",),
            source="summary_csv_exporter",
        )
