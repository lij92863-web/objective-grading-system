"""Item-analysis CSV exporter — matches legacy ``write_item_analysis``.

Does NOT import legacy, web, or any grading/recognition module.
Only writes pre-computed item-analysis rows to CSV.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

# Must match legacy write_item_analysis field order exactly.
ITEM_ANALYSIS_FIELDNAMES = [
    "question",
    "question_id",
    "question_status",
    "difficulty",
    "tags",
    "answer",
    "points",
    "accuracy",
    "blank_rate",
    "wrong_rate",
    "partial_rate",
    "invalid_rate",
    "option_distribution",
]


class ItemAnalysisCsvExporter(ReportExporter):
    """Export an ``item_analysis.csv`` file from pre-computed rows.

    Usage::

        exporter = ItemAnalysisCsvExporter()
        result = exporter.export(
            ExportRequest(output_dir=Path("./out")),
            rows,   # list of dicts with ITEM_ANALYSIS_FIELDNAMES keys
        )
    """

    def export(
        self,
        request: ExportRequest,
        data: object,
        fieldnames: Optional[List[str]] = None,
    ) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(ITEM_ANALYSIS_FIELDNAMES)

        rows: List[Dict[str, object]] = []
        if isinstance(data, list):
            rows = data

        if not rows:
            out_path = request.output_dir / "item_analysis.csv"
            write_dict_rows_csv(out_path, [], fieldnames=fieldnames)
            return ExportResult(
                status="ok",
                generated_files=("item_analysis.csv",),
                warnings=("item_analysis_rows_empty",),
                source="item_analysis_csv_exporter",
            )

        out_path = request.output_dir / "item_analysis.csv"
        write_dict_rows_csv(out_path, rows, fieldnames=fieldnames)
        return ExportResult(
            status="ok",
            generated_files=("item_analysis.csv",),
            source="item_analysis_csv_exporter",
        )
