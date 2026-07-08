"""Exporter contracts — interfaces for Stage E1+ migration.

These define the shapes that future concrete exporters must fulfil.
No real file I/O or legacy imports here — purely interface definitions.
"""

import dataclasses
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


@dataclasses.dataclass(frozen=True)
class ExportRequest:
    """Input for a single export operation."""

    output_dir: Path = Path(".")
    exam_name: str = ""
    class_name: str = ""
    subject: str = ""
    exam_date: str = ""
    run_id: str = ""


@dataclasses.dataclass(frozen=True)
class ExportResult:
    """Outcome of a single export operation."""

    status: str = "ok"          # "ok" | "partial" | "error"
    generated_files: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    source: str = ""            # e.g. "summary_exporter"


class ReportExporter(ABC):
    """Abstract exporter — one concrete class per output format.

    Each exporter receives an ``ExportRequest`` plus domain data and
    returns an ``ExportResult``.  The caller is responsible for
    providing correctly-typed domain objects (StudentResult,
    KnowledgeProfile, etc.).
    """

    @abstractmethod
    def export(self, request: ExportRequest, data: object) -> ExportResult:
        """Run the export and return a result.

        *data* is domain-specific (list of StudentResult, dict, etc.)
        and is validated by the concrete implementation.
        """
        ...
