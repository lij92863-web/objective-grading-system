"""Data models used by the objective grader.

The first modular pass keeps the existing dataclasses as the single source of
truth so old scripts and new web routes behave exactly the same.
"""

from objective_grader_legacy import AnswerKey, BankQuestion, ExamMeta, KnowledgeProfile, QuestionResult, QuestionSpec, StudentResult, Submission

__all__ = [
    "AnswerKey",
    "BankQuestion",
    "ExamMeta",
    "KnowledgeProfile",
    "QuestionResult",
    "QuestionSpec",
    "StudentResult",
    "Submission",
]

