"""Validation-report CSV exporter.

Matches legacy ``write_validation_report`` output.
Only writes pre-computed rows — does NOT build the report.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

VALIDATION_REPORT_FIELDNAMES = ["severity", "scope", "item", "message"]


class ValidationReportCsvExporter(ReportExporter):
    def export(self, request: ExportRequest, data: object,
               fieldnames: Optional[List[str]] = None) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(VALIDATION_REPORT_FIELDNAMES)
        rows: List[Dict[str, object]] = data if isinstance(data, list) else []
        if not rows:
            write_dict_rows_csv(request.output_dir / "validation_report.csv", [], fieldnames=fieldnames)
            return ExportResult(status="ok", generated_files=("validation_report.csv",),
                                warnings=("validation_report_rows_empty",), source="validation_report_csv_exporter")
        write_dict_rows_csv(request.output_dir / "validation_report.csv", rows, fieldnames=fieldnames)
        return ExportResult(status="ok", generated_files=("validation_report.csv",),
                            source="validation_report_csv_exporter")
