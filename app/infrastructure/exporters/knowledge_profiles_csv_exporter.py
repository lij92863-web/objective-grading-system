"""Knowledge-profiles CSV exporter.

Matches legacy ``write_knowledge_profiles`` output.
Only writes pre-computed rows — does NOT run analysis.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .contracts import ExportRequest, ExportResult, ReportExporter
from .csv_helpers import write_dict_rows_csv

KNOWLEDGE_PROFILES_FIELDNAMES = [
    "student_id", "name", "tag", "score", "max_score",
    "mastery", "mastery_level", "question_count", "weak",
]


class KnowledgeProfilesCsvExporter(ReportExporter):
    def export(self, request: ExportRequest, data: object,
               fieldnames: Optional[List[str]] = None) -> ExportResult:
        if fieldnames is None:
            fieldnames = list(KNOWLEDGE_PROFILES_FIELDNAMES)
        rows: List[Dict[str, object]] = data if isinstance(data, list) else []
        if not rows:
            write_dict_rows_csv(request.output_dir / "knowledge_profile.csv", [], fieldnames=fieldnames)
            return ExportResult(status="ok", generated_files=("knowledge_profile.csv",),
                                warnings=("knowledge_profiles_rows_empty",), source="knowledge_profiles_csv_exporter")
        write_dict_rows_csv(request.output_dir / "knowledge_profile.csv", rows, fieldnames=fieldnames)
        return ExportResult(status="ok", generated_files=("knowledge_profile.csv",),
                            source="knowledge_profiles_csv_exporter")
