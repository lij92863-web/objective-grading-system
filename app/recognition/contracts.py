"""Recognition contracts — pure dataclasses. No legacy/compat/grading imports."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ImageAsset:
    asset_id: str = ""
    file_path: str = ""
    sha256: str = ""
    mime_type: str = ""
    source_kind: str = "fixture"
    created_at: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    page: Optional[int] = None


@dataclass
class ImageQualityReport:
    asset_id: str = ""
    is_valid: bool = False
    status: str = "unknown"
    reasons: List[str] = field(default_factory=list)
    sha256: str = ""
    mime_type: str = ""
    file_size: int = 0


@dataclass
class QuestionROI:
    question_number: int = 0
    question_type: str = "choice"
    roi_box: Dict[str, int] = field(default_factory=dict)
    expected_answer: Optional[str] = None
    points: float = 1.0
    tags: List[str] = field(default_factory=list)
    engine_hint: str = ""


@dataclass
class AnswerSheetLayout:
    layout_id: str = ""
    version: str = "1.0"
    page_count: int = 1
    coordinate_space: str = "pixel"
    identity_roi: Dict[str, int] = field(default_factory=dict)
    question_rois: List[QuestionROI] = field(default_factory=list)


@dataclass
class RecognitionRunConfig:
    run_id: str = ""
    dry_run: bool = True
    allow_real_api: bool = False
    qwen_enabled: bool = False
    auto_accept_threshold: float = 0.90
    low_confidence_threshold: float = 0.60
    require_teacher_confirmation: bool = True
    max_real_api_calls: int = 0
    fail_closed: bool = True


@dataclass
class RecognitionRequestItem:
    question_number: int = 0
    question_type: str = "choice"
    roi_box: Dict[str, int] = field(default_factory=dict)
    expected_answer: Optional[str] = None
    points: float = 1.0
    tags: List[str] = field(default_factory=list)
    engine_hint: str = ""


@dataclass
class RecognitionRequestBatch:
    run_id: str = ""
    asset_id: str = ""
    layout_id: str = ""
    items: List[RecognitionRequestItem] = field(default_factory=list)
    config: RecognitionRunConfig = field(default_factory=RecognitionRunConfig)


@dataclass
class EngineCandidate:
    question_number: int = 0
    engine: str = ""
    value: str = ""
    normalized_value: str = ""
    latex: str = ""
    confidence: float = 0.0
    status: str = ""
    reason: str = ""
    raw_ref: str = ""
    roi_box: Dict[str, int] = field(default_factory=dict)


@dataclass
class RecognitionDecision:
    question_number: int = 0
    value: str = ""
    normalized_value: str = ""
    latex: str = ""
    status: str = "needs_review"
    confidence: float = 0.0
    source_engines: List[str] = field(default_factory=list)
    needs_review: bool = True
    blocking: bool = False
    reason: str = ""
    candidates: List[EngineCandidate] = field(default_factory=list)


@dataclass
class RecognizedSubmissionDraft:
    student_id: str = ""
    student_number: str = ""
    student_name: str = ""
    identity_status: str = "missing"
    decisions: List[RecognitionDecision] = field(default_factory=list)
    exceptions: List[Dict] = field(default_factory=list)
    ready_for_confirmation: bool = False
    ready_for_grading: bool = False


@dataclass
class RecognitionRunResult:
    run_id: str = ""
    asset_id: str = ""
    status: str = ""
    drafts: List[RecognizedSubmissionDraft] = field(default_factory=list)
    exception_queue: List[Dict] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    config: RecognitionRunConfig = field(default_factory=RecognitionRunConfig)


@dataclass
class TeacherConfirmationItem:
    question_number: int = 0
    original_value: str = ""
    confirmed_value: str = ""
    status: str = ""


@dataclass
class TeacherConfirmedSubmission:
    student_id: str = ""
    name: str = ""
    answers: Dict[int, str] = field(default_factory=dict)
    confirmed_at: str = ""
    confirmed_by: str = ""
    source_draft_id: str = ""
