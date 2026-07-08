"""Grading core: models, answer normalization, scoring, and student grading."""

from app.domain.grading import (  # noqa: F401
    AnswerKey,
    QuestionResult,
    QuestionSpec,
    StudentResult,
    Submission,
    allowed_options,
    format_answer,
    format_expected_answer,
    grade_all,
    grade_submission,
    is_choice_answer,
    is_choice_like_answer,
    matches_text_answer,
    normalize_answer,
    normalize_text_answer,
    score_answer,
    score_answer_detail,
)
from app.domain.grading.normalize import parse_question_number  # noqa: F401
from legacy.objective_grader_legacy import (  # noqa: F401
    BankQuestion,
    CHOICE_OPTIONS,
    ExamMeta,
    KnowledgeProfile,
    QUESTION_STATUSES,
    competition_ranks,
    load_answer_key,
    load_question_bank,
    load_submissions,
)
