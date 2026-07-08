"""Recognition mock pipeline (Stage R2-R7).

Ties together identity parsing, choice/blank normalisation, Qwen judgment
mocking, and exception-queue collection into a single callable batch
function.
"""

import dataclasses
from typing import Dict, Iterable, List, Optional

from .blank_mock import normalize_blank_recognition
from .choice_mock import normalize_choice_recognition
from .exception_queue import build_exception_queue
from .identity_parser import parse_student_identity
from .models import (
    ChoiceCellOutput,
    MockBlankOutput,
    QwenJudgmentMock,
    RecognitionException,
    RecognizedAnswerDraft,
    StudentIdentityCandidate,
)
from .qwen_judgment_mock import should_auto_accept_qwen_judgment


@dataclasses.dataclass(frozen=True)
class MockPipelineResult:
    """Aggregated output of a mock recognition batch."""

    identity: Optional[StudentIdentityCandidate] = None
    drafts: List[RecognizedAnswerDraft] = dataclasses.field(default_factory=list)
    auto_accepted: List[RecognizedAnswerDraft] = dataclasses.field(
        default_factory=list
    )
    exceptions: List[RecognitionException] = dataclasses.field(default_factory=list)
    judgments: List[QwenJudgmentMock] = dataclasses.field(default_factory=list)

    # summary counts
    total_drafts: int = 0
    auto_accepted_count: int = 0
    exception_count: int = 0
    low_confidence_count: int = 0
    needs_review_count: int = 0


def process_mock_recognition_batch(
    identity_raw_text: str,
    roster: Optional[Dict[str, str]] = None,
    choice_cell_outputs: Optional[Dict[int, ChoiceCellOutput]] = None,
    blank_outputs: Optional[Dict[int, MockBlankOutput]] = None,
    qwen_judgments: Optional[Dict[int, QwenJudgmentMock]] = None,
    auto_accept_threshold: float = 0.90,
    choice_low_confidence_threshold: float = 0.80,
    blank_low_confidence_threshold: float = 0.80,
) -> MockPipelineResult:
    """Run a full mock recognition batch.

    Parameters
    ----------
    identity_raw_text:
        The OCR result from the name field, e.g. ``"1李明"``.
    roster:
        Optional ``{student_id: name}`` mapping for validation.
    choice_cell_outputs:
        ``{question_number: ChoiceCellOutput}`` mapping.
    blank_outputs:
        ``{question_number: MockBlankOutput}`` mapping.
    qwen_judgments:
        ``{question_number: QwenJudgmentMock}`` mapping for complex blanks.
    auto_accept_threshold:
        Minimum confidence for auto-accepting a Qwen judgment.
    choice_low_confidence_threshold:
        Threshold for choice recognition.
    blank_low_confidence_threshold:
        Threshold for blank recognition.
    """
    choice_cell_outputs = choice_cell_outputs or {}
    blank_outputs = blank_outputs or {}
    qwen_judgments = qwen_judgments or {}

    # -- 1. identity ---------------------------------------------------------
    identity = parse_student_identity(identity_raw_text, roster=roster)

    # -- 2. choice drafts ---------------------------------------------------
    drafts: List[RecognizedAnswerDraft] = []
    for qnum, cell in sorted(choice_cell_outputs.items()):
        draft = normalize_choice_recognition(
            cell, question_number=qnum, low_confidence_threshold=choice_low_confidence_threshold
        )
        # Attach identity info if confirmed
        if identity.status == StudentIdentityCandidate.STATUS_CONFIRMED:
            draft = dataclasses.replace(
                draft,
                student_id=identity.matched_student_id,
                student_name=identity.student_name,
                student_number=identity.student_number,
            )
        drafts.append(draft)

    # -- 3. blank drafts ----------------------------------------------------
    for qnum, mock in sorted(blank_outputs.items()):
        draft = normalize_blank_recognition(
            mock, question_number=qnum, low_confidence_threshold=blank_low_confidence_threshold
        )
        if identity.status == StudentIdentityCandidate.STATUS_CONFIRMED:
            draft = dataclasses.replace(
                draft,
                student_id=identity.matched_student_id,
                student_name=identity.student_name,
                student_number=identity.student_number,
            )
        drafts.append(draft)

    # -- 4. Qwen judgments & auto-accept ------------------------------------
    judgments: List[QwenJudgmentMock] = []
    auto_accepted: List[RecognizedAnswerDraft] = []
    for qnum, judgment in sorted(qwen_judgments.items()):
        judgments.append(judgment)
        # find the matching draft
        matching_draft = next((d for d in drafts if d.question_number == qnum), None)
        if should_auto_accept_qwen_judgment(
            judgment, draft=matching_draft, threshold=auto_accept_threshold
        ):
            if matching_draft is not None:
                accepted_draft = dataclasses.replace(
                    matching_draft,
                    status=RecognizedAnswerDraft.STATUS_AUTO_ACCEPTED,
                    needs_review=False,
                )
                # Replace in drafts list
                drafts[:] = [
                    accepted_draft if d.question_number == qnum else d
                    for d in drafts
                ]
                auto_accepted.append(accepted_draft)

    # -- 5. exception queue --------------------------------------------------
    exceptions = build_exception_queue(
        drafts,
        identity=identity,
        judgments=judgments,
        judgment_threshold=auto_accept_threshold,
    )

    # -- 6. summary ----------------------------------------------------------
    total_drafts = len(drafts)
    auto_accepted_count = len(auto_accepted)
    exception_count = len(exceptions)
    low_confidence_count = sum(
        1 for d in drafts if d.status == RecognizedAnswerDraft.STATUS_LOW_CONFIDENCE
    )
    needs_review_count = sum(1 for d in drafts if d.needs_review)

    return MockPipelineResult(
        identity=identity,
        drafts=drafts,
        auto_accepted=auto_accepted,
        exceptions=exceptions,
        judgments=judgments,
        total_drafts=total_drafts,
        auto_accepted_count=auto_accepted_count,
        exception_count=exception_count,
        low_confidence_count=low_confidence_count,
        needs_review_count=needs_review_count,
    )
