"""Capture job model and store.

Persists the raw image and its metadata into the fixed tree required by the
constitution (§4)::

    data/captures/jobs/<id>/
        original.jpg
        original.sha256
        manifest.json
        events.jsonl
        normalized/ crops/ recognition/ review/ confirmed/

All writes go through ``atomic_io`` (crash-safe) and ``safe_paths`` (traversal
safe). This module ONLY ingests and stores; it never recognizes or grades, and
it must not import ``omr`` or ``grading_bridge``.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.student_recognition.capture.camera_device_contract import (
    SOURCE_BROWSER,
    assert_supported_source,
)
from app.student_recognition.common import atomic_io, ids, safe_paths
from app.student_recognition.common.artifact_manifest import (
    SCHEMA_VERSION,
    ArtifactManifest,
)
from app.student_recognition.common.timeutil import now_iso
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.state_model import State

ARTIFACT_ORIGINAL = "original.jpg"
ARTIFACT_SHA256 = "original.sha256"
ARTIFACT_MANIFEST = "manifest.json"
ARTIFACT_EVENTS = "events.jsonl"

SUBDIRS = ("normalized", "crops", "recognition", "review", "confirmed")


@dataclass
class CaptureJob:
    """In-memory capture job. Mirrors the on-disk manifest + events."""

    job_id: str
    status: State = State.JOB_CREATED
    sha256: str = ""
    source: str = SOURCE_BROWSER
    created_at: str = ""
    updated_at: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def append_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self.events.append(
            {"type": event_type, "payload": payload or {}, "at": now_iso()}
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "job_id": self.job_id,
            "status": self.status.value,
            "sha256": self.sha256,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": list(self.events),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CaptureJob":
        return cls(
            job_id=d["job_id"],
            status=State(d["status"]),
            sha256=d.get("sha256", ""),
            source=d.get("source", SOURCE_BROWSER),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            events=list(d.get("events", [])),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
        )


class CaptureJobStore:
    """Persists capture jobs to the fixed tree (idempotent via sha256)."""

    def __init__(self, root: Optional[Path] = None):
        # ``root`` overrides the captures root (tests use a temp dir).
        self.root = Path(root) if root is not None else None

    # -- path helpers -------------------------------------------------------
    def _jobs_root(self) -> Path:
        if self.root is not None:
            return safe_paths.safe_join(self.root, "jobs")
        return safe_paths.job_dir("").parent  # jobs/ directory

    def _job_dir(self, job_id: str) -> Path:
        if self.root is not None:
            return safe_paths.safe_join(self.root, "jobs", job_id)
        return safe_paths.job_dir(job_id)

    # -- public API ---------------------------------------------------------
    def create(
        self,
        image_bytes: bytes,
        source: str = SOURCE_BROWSER,
        job_id: Optional[str] = None,
    ) -> CaptureJob:
        assert_supported_source(source)
        sha = ids.compute_sha256(image_bytes)

        # Idempotency: re-upload of the same image returns the first job (§6).
        index = ids.DedupIndex(self.root)
        if index.seen(sha):
            existing = index.lookup(sha)
            return self.get(existing)

        if job_id is None:
            job_id = ids.new_job_id()
        job_dir = self._job_dir(job_id)
        safe_paths.ensure_dir(job_dir)
        for sub in SUBDIRS:
            safe_paths.ensure_dir(job_dir / sub)

        atomic_io.atomic_write_bytes(job_dir / ARTIFACT_ORIGINAL, image_bytes)
        atomic_io.atomic_write_text(job_dir / ARTIFACT_SHA256, sha)

        job = CaptureJob(
            job_id=job_id,
            status=State.JOB_CREATED,
            sha256=sha,
            source=source,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        job.append_event("created", {"source": source, "sha256": sha})
        self.persist(job)
        self._append_event_line(job_id, job.events[-1])
        index.record(sha, job_id)
        return job

    def persist(self, job: CaptureJob) -> None:
        job_dir = self._job_dir(job.job_id)
        manifest = ArtifactManifest(
            job_id=job.job_id,
            source=job.source,
            status=job.status.value,
            sha256=job.sha256,
            created_at=job.created_at,
            updated_at=now_iso(),
            files={"original": ARTIFACT_ORIGINAL, "sha256": ARTIFACT_SHA256},
        )
        atomic_io.atomic_write_json(job_dir / ARTIFACT_MANIFEST, manifest.to_dict())

    def _append_event_line(self, job_id: str, event: Dict[str, Any]) -> None:
        job_dir = self._job_dir(job_id)
        atomic_io.atomic_append_line(
            job_dir / ARTIFACT_EVENTS, json.dumps(event, ensure_ascii=False)
        )

    def append_event(self, job_id: str, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        event = {"type": event_type, "payload": payload or {}, "at": now_iso()}
        self._append_event_line(job_id, event)

    def get(self, job_id: str) -> CaptureJob:
        job_dir = self._job_dir(job_id)
        manifest_path = job_dir / ARTIFACT_MANIFEST
        events_path = job_dir / ARTIFACT_EVENTS
        if not manifest_path.exists():
            raise FileNotFoundError(f"no capture job {job_id!r}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        job = CaptureJob.from_dict(manifest)
        if events_path.exists():
            job.events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        return job

    def exists(self, job_id: str) -> bool:
        return self._job_dir(job_id).joinpath(ARTIFACT_MANIFEST).exists()

    def list_job_ids(self) -> List[str]:
        base = self._jobs_root()
        if not base.exists():
            return []
        out = []
        for p in base.iterdir():
            if p.is_dir():
                try:
                    safe_paths.validate_job_id(p.name)
                except ValueError:
                    continue
                if self.exists(p.name):
                    out.append(p.name)
        return sorted(out)
