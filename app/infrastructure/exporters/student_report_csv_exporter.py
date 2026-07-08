"""Student-report CSV exporter.

Matches legacy ``write_student_report`` output.
Only writes pre-computed rows — does NOT analyse students.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

STUDENT_REPORT_FIELDNAMES = [
    "student_id", "name", "score", "max_score", "percent", "rank",
    "weak_tags", "wrong_questions", "partial_questions", "blank_questions", "invalid_questions",
]


class StudentReportCsvExporter(ReportExporter):
    def export(self, request: ExportRequest, data: object,
               fieldnames: Optional[List[str]] = None) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(STUDENT_REPORT_FIELDNAMES)
        rows: List[Dict[str, object]] = data if isinstance(data, list) else []
        if not rows:
            write_dict_rows_csv(request.output_dir / "student_report.csv", [], fieldnames=fieldnames)
            return ExportResult(status="ok", generated_files=("student_report.csv",),
                                warnings=("student_report_rows_empty",), source="student_report_csv_exporter")
        write_dict_rows_csv(request.output_dir / "student_report.csv", rows, fieldnames=fieldnames)
        return ExportResult(status="ok", generated_files=("student_report.csv",),
                            source="student_report_csv_exporter")
