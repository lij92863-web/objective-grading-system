"""Prompt builder — selects and builds prompts by prompt_type.

Reuses constants from ``app.recognition.prompts``.  For dynamic prompts
(complex_blank_judgment) the caller must supply ``standard_answer`` and
``student_answer`` via the request metadata.
"""

from .errors import QwenAdapterError, QwenAdapterErrorCode
from .models import (
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
    QwenRequest,
)


def build_prompt(request: QwenRequest) -> str:
    """Return the prompt string for *request*.

    For ``name_field``, ``choice_cell``, and ``blank_answer`` the prompt
    is taken directly from the constants in ``app.recognition.prompts``.

    For ``complex_blank_judgment`` the caller must supply
    ``standard_answer`` and ``student_answer`` in ``request.metadata``.
    """
    pt = request.prompt_type

    if pt == PROMPT_TYPE_NAME_FIELD:
        from ..prompts import NAME_FIELD_RECOGNITION_PROMPT
        return NAME_FIELD_RECOGNITION_PROMPT

    if pt == PROMPT_TYPE_CHOICE_CELL:
        from ..prompts import CHOICE_CELL_RECOGNITION_PROMPT
        return CHOICE_CELL_RECOGNITION_PROMPT

    if pt == PROMPT_TYPE_BLANK_ANSWER:
        from ..prompts import BLANK_ANSWER_RECOGNITION_PROMPT
        return BLANK_ANSWER_RECOGNITION_PROMPT

    if pt == PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT:
        from ..prompts import COMPLEX_BLANK_JUDGMENT_PROMPT
        template = COMPLEX_BLANK_JUDGMENT_PROMPT
    if pt == PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT:
        from ..prompts import COMPLEX_BLANK_JUDGMENT_PROMPT
        template = COMPLEX_BLANK_JUDGMENT_PROMPT
        meta = request.metadata or {}
        standard = meta.get("standard_answer", "")
        student = meta.get("student_answer", "")
        stem = meta.get("question_text", "")
        points = meta.get("points", "")
        ocr_conf = meta.get("ocr_confidence", "")
        fmt_req = meta.get("format_required", "")
        # Use replace to avoid conflicts with JSON braces in the template
        return (
            template
            .replace("{stem}", str(stem))
            .replace("{points}", str(points))
            .replace("{correct_answer}", str(standard))
            .replace("{student_answer}", str(student))
            .replace("{ocr_confidence}", str(ocr_conf))
            .replace("{format_required}", str(fmt_req))
        )

    raise QwenAdapterError(
        QwenAdapterErrorCode.UNSUPPORTED_PROMPT_TYPE,
        f"Unsupported prompt_type: {pt!r}",
    )
