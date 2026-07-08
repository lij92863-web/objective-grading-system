"""Independent grading foundation used by legacy and app entry points."""

from .answer_draft import (
    AnswerDraft,
    DraftAnswerItem,
    DraftStatus,
    confirm_draft_answer,
    draft_to_submission,
    mark_low_confidence,
)
from .models import AnswerKey, QuestionResult, QuestionSpec, SingleQuestionScore, StudentResult, Submission
from .normalize import (
    allowed_options,
    format_answer,
    format_expected_answer,
    is_choice_answer,
    is_choice_like_answer,
    matches_text_answer,
    normalize_answer,
    normalize_text_answer,
)
from .precheck import PrecheckIssue, PrecheckReport, run_grading_precheck
from .scoring import grade_all, grade_submission, score_answer, score_answer_detail

__all__ = [
    "AnswerDraft",
    "AnswerKey",
    "DraftAnswerItem",
    "DraftStatus",
    "PrecheckIssue",
    "PrecheckReport",
    "QuestionResult",
    "QuestionSpec",
    "SingleQuestionScore",
    "StudentResult",
    "Submission",
    "allowed_options",
    "confirm_draft_answer",
    "draft_to_submission",
    "format_answer",
    "format_expected_answer",
    "grade_all",
    "grade_submission",
    "is_choice_answer",
    "is_choice_like_answer",
    "mark_low_confidence",
    "matches_text_answer",
    "normalize_answer",
    "normalize_text_answer",
    "run_grading_precheck",
    "score_answer",
    "score_answer_detail",
]
