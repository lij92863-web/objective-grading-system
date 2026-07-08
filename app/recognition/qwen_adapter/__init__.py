"""Qwen adapter shell — Stage R8A.

Defines the abstract client interface, fake client, request/response
models, parser, validators, and mapping layer.  No real API calls are
made at this stage.
"""

from .client import QwenClient
from .errors import QwenAdapterError, QwenAdapterErrorCode
from .fake_client import FakeQwenClient
from .mapping import (
    parse_blank_response_to_draft,
    parse_choice_response_to_draft,
    parse_complex_judgment_response,
    parse_name_field_to_identity_candidate,
)
from .models import (
    QwenImageInput,
    QwenParsedResult,
    QwenRawResponse,
    QwenRequest,
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
)
from .parser import parse_qwen_response
from .validators import (
    validate_blank_answer_response,
    validate_choice_cell_response,
    validate_complex_blank_judgment_response,
    validate_name_field_response,
)

__all__ = [
    # client
    "QwenClient",
    "FakeQwenClient",
    # errors
    "QwenAdapterError",
    "QwenAdapterErrorCode",
    # models
    "QwenImageInput",
    "QwenRequest",
    "QwenRawResponse",
    "QwenParsedResult",
    "PROMPT_TYPE_NAME_FIELD",
    "PROMPT_TYPE_CHOICE_CELL",
    "PROMPT_TYPE_BLANK_ANSWER",
    "PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT",
    # parser
    "parse_qwen_response",
    # validators
    "validate_name_field_response",
    "validate_choice_cell_response",
    "validate_blank_answer_response",
    "validate_complex_blank_judgment_response",
    # mapping
    "parse_name_field_to_identity_candidate",
    "parse_choice_response_to_draft",
    "parse_blank_response_to_draft",
    "parse_complex_judgment_response",
]
