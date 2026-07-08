"""Report-builder contracts — pure dataclasses, no logic or I/O."""

import dataclasses
from typing import Dict, List, Optional, Set, Tuple


@dataclasses.dataclass(frozen=True)
class ReportBuildResult:
    """Output of a single report-data builder."""
    rows: tuple = ()
    fieldnames: tuple = ()
    warnings: tuple = ()


@dataclasses.dataclass(frozen=True)
class ReportRowsBundle:
    """Aggregated output of all builders for a grading run."""
    summary_rows: tuple = ()
    detail_rows: tuple = ()
    item_analysis_rows: tuple = ()
    knowledge_profiles: tuple = ()
    class_report_rows: tuple = ()
    validation_report_rows: tuple = ()
    practice_rows: tuple = ()
    student_report_rows: tuple = ()
