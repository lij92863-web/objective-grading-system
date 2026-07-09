"""Recognition job orchestration (constitution §2 / §14).

``RecognitionJob`` drives a single capture through the layers: it ingests the
image via ``CaptureJobStore``, advances the capture-layer states, and builds a
``RecognitionDraft`` which it validates into ``blocking_errors`` / ``review_items``.

This module DELEGATES all real work to the capture / drafts / identity / state
modules. It contains no OMR, image-processing or grading code (the
"pipeline contains no business algorithms" rule).
"""

from typing import Any, Dict, List, Optional

from app.student_recognition.capture.capture_job import CaptureJob, CaptureJobStore
from app.student_recognition.common.timeutil import now_iso
from app.student_recognition.drafts.draft_validator import validate
from app.student_recognition.drafts.recognition_draft import RecognitionDraft
from app.student_recognition.identity_contract import parse_identity
from app.student_recognition.pipeline.state_machine import apply_transition
from app.student_recognition.state_model import State

# Capture-layer pipeline order (stub: image/OMR algorithms filled later).
_CAPTURE_STEPS = [
    State.UPLOADED,
    State.IMAGE_QUALITY_CHECKED,
    State.PAGE_LOCATED,
    State.NORMALIZED,
    State.CROPS_GENERATED,
    State.ROI_MAPPED,
    State.OMR_RECOGNIZED,
]


class RecognitionJob:
    def __init__(self, store: Optional[CaptureJobStore] = None):
        self.store = store or CaptureJobStore()

    def ingest(
        self,
        image_bytes: bytes,
        source: str = "browser",
        job_id: Optional[str] = None,
    ) -> CaptureJob:
        job = self.store.create(image_bytes, source=source, job_id=job_id)
        for step in _CAPTURE_STEPS:
            apply_transition(job, step)
        self.store.persist(job)
        return job

    def build_draft(
        self,
        job: CaptureJob,
        identity_raw: Optional[str] = None,
        candidates: Optional[Dict[str, Any]] = None,
        roster: Optional[Dict[str, str]] = None,
    ) -> RecognitionDraft:
        draft = RecognitionDraft(
            job_id=job.job_id,
            status=State.DRAFT_CREATED,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        if identity_raw is not None:
            draft.identity = parse_identity(identity_raw).to_dict()
        if candidates is not None:
            draft.candidates = candidates

        blocking, reviews = validate(draft, roster=roster)
        draft.blocking_errors = blocking
        draft.review_items = reviews

        if blocking:
            apply_transition(draft, State.DRAFT_BLOCKED)
        elif reviews:
            apply_transition(draft, State.DRAFT_HAS_REVIEW_ITEMS)
        else:
            apply_transition(draft, State.DRAFT_CLEAN)

        draft.append_event(
            "draft_built", {"blocking": len(blocking), "review": len(reviews)}
        )
        return draft

    def process(
        self,
        image_bytes: bytes,
        source: str = "browser",
        job_id: Optional[str] = None,
        identity_raw: Optional[str] = None,
        candidates: Optional[Dict[str, Any]] = None,
        roster: Optional[Dict[str, str]] = None,
    ) -> tuple[CaptureJob, RecognitionDraft]:
        job = self.ingest(image_bytes, source=source, job_id=job_id)
        draft = self.build_draft(
            job, identity_raw=identity_raw, candidates=candidates, roster=roster
        )
        return job, draft
