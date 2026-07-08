"""Class-report CSV exporter.

Matches legacy ``write_class_report`` output.
Only writes pre-computed rows — does NOT build the report.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

CLASS_REPORT_FIELDNAMES = ["section", "metric", "value", "extra"]


class ClassReportCsvExporter(ReportExporter):
    def export(self, request: ExportRequest, data: object,
               fieldnames: Optional[List[str]] = None) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(CLASS_REPORT_FIELDNAMES)
        rows: List[Dict[str, object]] = data if isinstance(data, list) else []
        if not rows:
            write_dict_rows_csv(request.output_dir / "class_report.csv", [], fieldnames=fieldnames)
            return ExportResult(status="ok", generated_files=("class_report.csv",),
                                warnings=("class_report_rows_empty",), source="class_report_csv_exporter")
        write_dict_rows_csv(request.output_dir / "class_report.csv", rows, fieldnames=fieldnames)
        return ExportResult(status="ok", generated_files=("class_report.csv",),
                            source="class_report_csv_exporter")
