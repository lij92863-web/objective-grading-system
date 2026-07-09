"""ExamMeta — mirrors legacy.ExamMeta without importing legacy.

Fields and defaults match ``legacy.objective_grader_legacy.ExamMeta`` exactly.
"""

from dataclasses import dataclass


@dataclass
class ExamMeta:
    """Metadata about a single grading run."""
    exam_name: str = ""
    class_name: str = ""
    subject: str = ""
    exam_date: str = ""
