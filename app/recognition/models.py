"""Recognition data structures — Stage R2-R7.

These models represent the mock recognition pipeline's data contracts.
They are compatible with the existing ``DraftAnswerItem`` in
``app.domain.grading.answer_draft`` and do not replace it.
"""

import dataclasses
from typing import Dict, FrozenSet, List, Optional, Tuple


# ---------------------------------------------------------------------------
# ROI box
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ROIBox:
    """Image region-of-interest coordinates.

    This is a pure data structure; no real image cropping is done at this
    stage.
    """

    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    page: int = 1
    label: str = ""


# ---------------------------------------------------------------------------
# Mock inputs (what Qwen would return)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ChoiceCellOutput:
    """Mock of a Qwen choice-cell recognition result."""

    answer: str = ""
    confidence: float = 0.0


@dataclasses.dataclass(frozen=True)
class MockBlankOutput:
    """Mock of a Qwen blank-answer OCR result."""

    raw_text: str = ""
    latex: str = ""
    confidence: float = 0.0
    status: str = "recognized"


# ---------------------------------------------------------------------------
# Recognition draft
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class RecognizedAnswerDraft:
    """AI / OCR recognition draft — NOT a final score.

    This is the central data structure flowing through the recognition
    pipeline.  After teacher confirmation or auto-acceptance it is
    converted into a ``DraftAnswerItem`` and then into a ``Submission``
    for the existing grading core.
    """

    question_number: int = 0
    question_type: str = ""
    raw_text: str = ""
    normalized_text: str = ""
    latex: str = ""
    candidate_answers: Tuple[str, ...] = ()
    confidence: float = 0.0
    source: str = "manual"
    status: str = "draft"
    message: str = ""
    needs_review: bool = False
    # optional contextual fields
    student_id: str = ""
    student_number: str = ""
    student_name: str = ""
    roi_box: Optional[ROIBox] = None
    raw_image_ref: str = ""

    # ------------------------------------------------------------------
    # status constants (mirrored from DraftStatus where applicable)
    # ------------------------------------------------------------------
    STATUS_DRAFT = "draft"
    STATUS_CONFIRMED = "confirmed"
    STATUS_AUTO_ACCEPTED = "auto_accepted"
    STATUS_LOW_CONFIDENCE = "low_confidence"
    STATUS_CONFLICT = "conflict"
    STATUS_BLANK = "blank"
    STATUS_INVALID = "invalid"
    STATUS_UNCLEAR = "unclear"
    STATUS_NEEDS_REVIEW = "needs_review"

    # ------------------------------------------------------------------
    # source constants
    # ------------------------------------------------------------------
    SOURCE_MANUAL = "manual"
    SOURCE_EXCEL = "excel"
    SOURCE_PASTE = "paste"
    SOURCE_QWEN_MOCK = "qwen_mock"
    SOURCE_OCR_MOCK = "ocr_mock"


# ---------------------------------------------------------------------------
# Choice recognition result (intermediate)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ChoiceRecognitionResult:
    """Normalised choice recognition output."""

    original_answer: str = ""
    normalized_answer: str = ""
    confidence: float = 0.0
    status: str = "draft"
    message: str = ""


# ---------------------------------------------------------------------------
# Student identity
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class StudentIdentityCandidate:
    """Parsed name-field identity with roster-validation result."""

    raw_text: str = ""
    student_number: str = ""
    student_name: str = ""
    status: str = "draft"
    confidence: float = 0.0
    message: str = ""
    matched_student_id: str = ""

    # status constants
    STATUS_CONFIRMED = "confirmed"
    STATUS_CONFLICT = "conflict"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_LOW_CONFIDENCE = "low_confidence"
    STATUS_INVALID = "invalid"


# ---------------------------------------------------------------------------
# Qwen judgment mock
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class QwenJudgmentMock:
    """Mock of a structured Qwen judgment for complex blank questions.

    verdict must be one of: correct, wrong, partial, needs_review, invalid.
    """

    verdict: str = "needs_review"
    confidence: float = 0.0
    reason: str = ""
    normalized_standard: str = ""
    normalized_student: str = ""
    equivalence_type: str = "unknown"
    requires_review: bool = True

    VERDICT_CORRECT = "correct"
    VERDICT_WRONG = "wrong"
    VERDICT_PARTIAL = "partial"
    VERDICT_NEEDS_REVIEW = "needs_review"
    VERDICT_INVALID = "invalid"

    VALID_VERDICTS: Tuple[str, ...] = (
        VERDICT_CORRECT,
        VERDICT_WRONG,
        VERDICT_PARTIAL,
        VERDICT_NEEDS_REVIEW,
        VERDICT_INVALID,
    )


# ---------------------------------------------------------------------------
# Exception queue item
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class RecognitionException:
    """A single item in the exception queue for teacher review."""

    code: str = ""
    level: str = "review"
    message: str = ""
    student_id: str = ""
    student_name: str = ""
    question_number: int = 0
    source: str = ""
    draft: Optional[RecognizedAnswerDraft] = None

    LEVEL_BLOCKING = "blocking"
    LEVEL_REVIEW = "review"
    LEVEL_WARNING = "warning"
