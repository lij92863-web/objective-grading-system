"""Practice-recommendations CSV exporter.

Matches legacy ``write_practice_recommendations`` output.
Only writes pre-computed rows — does NOT run recommendations.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

PRACTICE_RECOMMENDATIONS_FIELDNAMES = [
    "student_id", "name", "weak_tag", "mastery", "question_id",
    "target_difficulty", "difficulty", "difficulty_delta", "stem", "answer", "tags",
]


class PracticeRecommendationsCsvExporter(ReportExporter):
    def export(self, request: ExportRequest, data: object,
               fieldnames: Optional[List[str]] = None) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(PRACTICE_RECOMMENDATIONS_FIELDNAMES)
        rows: List[Dict[str, object]] = data if isinstance(data, list) else []
        if not rows:
            write_dict_rows_csv(request.output_dir / "practice_recommendations.csv", [], fieldnames=fieldnames)
            return ExportResult(status="ok", generated_files=("practice_recommendations.csv",),
                                warnings=("practice_recommendations_rows_empty",), source="practice_recommendations_csv_exporter")
        write_dict_rows_csv(request.output_dir / "practice_recommendations.csv", rows, fieldnames=fieldnames)
        return ExportResult(status="ok", generated_files=("practice_recommendations.csv",),
                            source="practice_recommendations_csv_exporter")
