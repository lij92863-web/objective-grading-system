"""Recognition mock pipeline — Stage R2-R7.

This package contains the mock data-flow for answer-sheet recognition
before real Qwen API integration. Every module uses deterministic rules
and mock data; no external API calls are made.
"""

from .models import (
    ChoiceCellOutput,
    ChoiceRecognitionResult,
    MockBlankOutput,
    QwenJudgmentMock,
    RecognitionException,
    RecognizedAnswerDraft,
    ROIBox,
    StudentIdentityCandidate,
)
from .identity_parser import parse_student_identity
from .choice_mock import normalize_choice_recognition
from .blank_mock import normalize_blank_recognition
from .qwen_judgment_mock import apply_qwen_judgment_mock, should_auto_accept_qwen_judgment
from .exception_queue import build_exception_queue
from .pipeline import MockPipelineResult, process_mock_recognition_batch
from .prompts import (
    BLANK_ANSWER_RECOGNITION_PROMPT,
    CHOICE_CELL_RECOGNITION_PROMPT,
    COMPLEX_BLANK_JUDGMENT_PROMPT,
    NAME_FIELD_RECOGNITION_PROMPT,
)

__all__ = [
    # models
    "ChoiceCellOutput",
    "ChoiceRecognitionResult",
    "MockBlankOutput",
    "QwenJudgmentMock",
    "RecognitionException",
    "RecognizedAnswerDraft",
    "ROIBox",
    "StudentIdentityCandidate",
    # identity
    "parse_student_identity",
    # choice
    "normalize_choice_recognition",
    # blank
    "normalize_blank_recognition",
    # qwen judgment mock
    "apply_qwen_judgment_mock",
    "should_auto_accept_qwen_judgment",
    # exception queue
    "build_exception_queue",
    # pipeline
    "MockPipelineResult",
    "process_mock_recognition_batch",
    # prompts
    "NAME_FIELD_RECOGNITION_PROMPT",
    "CHOICE_CELL_RECOGNITION_PROMPT",
    "BLANK_ANSWER_RECOGNITION_PROMPT",
    "COMPLEX_BLANK_JUDGMENT_PROMPT",
]
