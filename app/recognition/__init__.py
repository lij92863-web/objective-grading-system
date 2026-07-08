"""Recognition mock pipeline — Stage R2-R8A.

This package contains the mock data-flow for answer-sheet recognition
before real Qwen API integration. Every module uses deterministic rules
and mock data; no external API calls are made.

Stage R8A adds the ``qwen_adapter`` sub-package with an abstract client
interface, fake client, parser, validators, and mapping layer.
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

# -- Stage R8A: Qwen adapter shell -------------------------------------------

from .qwen_adapter import (  # noqa: E402
    FakeQwenClient,
    QwenAdapterError,
    QwenAdapterErrorCode,
    QwenClient,
    QwenImageInput,
    QwenParsedResult,
    QwenRawResponse,
    QwenRequest,
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
    parse_blank_response_to_draft,
    parse_choice_response_to_draft,
    parse_complex_judgment_response,
    parse_name_field_to_identity_candidate,
    parse_qwen_response,
    validate_blank_answer_response,
    validate_choice_cell_response,
    validate_complex_blank_judgment_response,
    validate_name_field_response,
)

__all__ = [
    # models (R2-R7)
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
    # -- Stage R8A qwen adapter --
    "QwenClient",
    "FakeQwenClient",
    "QwenAdapterError",
    "QwenAdapterErrorCode",
    "QwenImageInput",
    "QwenRequest",
    "QwenRawResponse",
    "QwenParsedResult",
    "PROMPT_TYPE_NAME_FIELD",
    "PROMPT_TYPE_CHOICE_CELL",
    "PROMPT_TYPE_BLANK_ANSWER",
    "PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT",
    "parse_qwen_response",
    "validate_name_field_response",
    "validate_choice_cell_response",
    "validate_blank_answer_response",
    "validate_complex_blank_judgment_response",
    "parse_name_field_to_identity_candidate",
    "parse_choice_response_to_draft",
    "parse_blank_response_to_draft",
    "parse_complex_judgment_response",
]
