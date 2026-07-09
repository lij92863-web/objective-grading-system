"""Thin API surface for the Student Recognition Engine.

This module is framework-agnostic: :class:`SREApi` validates input and delegates
to the engine modules. It contains **no** recognition / grading algorithms
(constitution §14 — web/API stays thin). A Flask ``Blueprint`` is provided
lazily when Flask is available; the engine does not depend on Flask being
installed. This module deliberately does NOT modify ``web_app.py``.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.student_recognition.capture.capture_job import CaptureJobStore
from app.student_recognition.drafts.recognition_draft import RecognitionDraft
from app.student_recognition.pipeline.recognition_job import RecognitionJob
from app.student_recognition.review.review_item import ReviewStatus
from app.student_recognition.review.review_queue import ReviewQueue
from app.student_recognition.state_model import State


class SREApi:
    def __init__(self, store: Optional[CaptureJobStore] = None, root: Optional[Path] = None):
        self.store = store or CaptureJobStore(root=root)
        self._job = RecognitionJob(store=self.store)

    def upload(
        self,
        image_bytes: bytes,
        source: str = "browser",
        job_id: Optional[str] = None,
        identity_raw: Optional[str] = None,
        candidates: Optional[Dict[str, Any]] = None,
        roster: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        job, draft = self._job.process(
            image_bytes,
            source=source,
            job_id=job_id,
            identity_raw=identity_raw,
            candidates=candidates,
            roster=roster,
        )
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "draft_status": draft.status.value,
            "blocking_errors": [c.value for c in draft.blocking_errors],
            "review_items": [r.to_dict() for r in draft.review_items],
        }

    def get_job(self, job_id: str) -> Dict[str, Any]:
        job = self.store.get(job_id)
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "sha256": job.sha256,
            "source": job.source,
        }

    def list_jobs(self) -> List[str]:
        return self.store.list_job_ids()

    def review_queue_from_draft(self, draft: RecognitionDraft) -> ReviewQueue:
        """Build a ``ReviewQueue`` from a draft's current review items."""
        q = ReviewQueue()
        for item in draft.review_items:
            q.enqueue(item)
        return q

    def resolve_review(
        self,
        queue: ReviewQueue,
        item_id: str,
        resolution: ReviewStatus,
        note: str = "",
        by: str = "",
    ) -> Optional[Any]:
        return queue.resolve(item_id, resolution, note=note, by=by)


def create_blueprint():
    """Return a Flask Blueprint wiring SREApi endpoints, or ``None`` if no Flask.

    Flask is optional for the engine; when absent this returns ``None`` and the
    engine still works (tests call :class:`SREApi` directly). Mounting into
    ``web_app.py`` is deferred to a later stage (registration pending).
    """
    try:
        from flask import Blueprint, jsonify, request
    except ImportError:
        return None

    bp = Blueprint("student_recognition", __name__)
    api = SREApi()

    @bp.route("/sre/upload", methods=["POST"])
    def upload():  # pragma: no cover - requires Flask at runtime
        data = request.get_data()
        source = request.form.get("source", "browser")
        identity_raw = request.form.get("identity_raw")
        return jsonify(api.upload(data, source=source, identity_raw=identity_raw))

    @bp.route("/sre/jobs/<job_id>", methods=["GET"])
    def job_status(job_id):  # pragma: no cover - requires Flask at runtime
        return jsonify(api.get_job(job_id))

    @bp.route("/sre/jobs", methods=["GET"])
    def list_jobs():  # pragma: no cover - requires Flask at runtime
        return jsonify({"jobs": api.list_jobs()})

    return bp
