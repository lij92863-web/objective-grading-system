"""Qwen adapter data structures — request / response / parsed-result models.

These are the adapter-layer contracts.  They wrap the raw API shapes
without coupling to the existing ``RecognizedAnswerDraft`` model (that
mapping lives in ``mapping.py``).
"""

import dataclasses
import uuid
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Prompt types
# ---------------------------------------------------------------------------

PROMPT_TYPE_NAME_FIELD = "name_field"
PROMPT_TYPE_CHOICE_CELL = "choice_cell"
PROMPT_TYPE_BLANK_ANSWER = "blank_answer"
PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT = "complex_blank_judgment"

VALID_PROMPT_TYPES: Tuple[str, ...] = (
    PROMPT_TYPE_NAME_FIELD,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
)

# ---------------------------------------------------------------------------
# Image input (test-friendly — no real file I/O)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class QwenImageInput:
    """Image to send to Qwen (mock-only at this stage).

    Safety: never log ``image_base64``.  Use ``image_path`` for log
    references only.
    """

    image_id: str = ""
    image_path: str = ""
    image_base64: str = ""
    mime_type: str = "image/jpeg"
    roi_box: Optional[object] = None   # ROIBox from recognition.models
    label: str = ""
    prompt_type: str = ""


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class QwenRequest:
    """A single request to the Qwen API (or fake client)."""

    request_id: str = ""
    prompt_type: str = ""
    prompt: str = ""
    image: Optional[QwenImageInput] = None
    metadata: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if not self.request_id:
            object.__setattr__(self, "request_id", uuid.uuid4().hex[:12])


# ---------------------------------------------------------------------------
# Raw response (what comes back from the API / fake client)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class QwenRawResponse:
    """Raw API response — before parsing and validation."""

    request_id: str = ""
    raw_text: str = ""
    parsed_json: Optional[dict] = None
    model: str = ""
    usage: Optional[dict] = None
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Parsed result (after validation, ready for mapping)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class QwenParsedResult:
    """Validated and typed result from a Qwen response.

    ``data`` holds the validated payload dict.  Callers should use the
    mapping layer to convert this into domain types
    (``StudentIdentityCandidate``, ``RecognizedAnswerDraft``, etc.).
    """

    prompt_type: str = ""
    status: str = "ok"
    data: dict = dataclasses.field(default_factory=dict)
    confidence: float = 0.0
    errors: List[str] = dataclasses.field(default_factory=list)
    warnings: List[str] = dataclasses.field(default_factory=list)
