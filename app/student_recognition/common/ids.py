"""ID generation and SHA-256 based idempotent de-duplication.

* ``new_job_id`` produces a globally unique capture job id.
* ``compute_sha256`` fingerprints raw image bytes.
* ``DedupIndex`` maps a sha256 to the first job that ingested it, so re-uploads
  are idempotent (constitution §6).
"""

import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict, Optional

from app.student_recognition.common import atomic_io, safe_paths


def new_job_id() -> str:
    """Return a unique capture job id (``job_<uuidhex>``)."""
    return "job_" + uuid.uuid4().hex


def compute_sha256(data: bytes) -> str:
    """Return the hex SHA-256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


class DedupIndex:
    """Maps image sha256 -> first job id. Backed by ``sha256_index.json``."""

    def __init__(self, root: Optional[Path] = None):
        self.path = safe_paths.sha256_index_path(root)
        self._cache: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._cache = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._cache = {}
        else:
            self._cache = {}

    def seen(self, sha256: str) -> bool:
        return sha256 in self._cache

    def lookup(self, sha256: str) -> Optional[str]:
        return self._cache.get(sha256)

    def record(self, sha256: str, job_id: str) -> None:
        self._cache[sha256] = job_id
        atomic_io.atomic_write_json(self.path, self._cache)

    def reset(self) -> None:
        self._cache = {}
        atomic_io.atomic_write_json(self.path, self._cache)
