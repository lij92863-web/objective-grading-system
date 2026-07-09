"""Artifact manifest model.

The manifest is the JSON metadata for a capture job. Per the constitution (§4,
§12) it MUST NOT contain base64 image data; it only references files by relative
path and carries structured metadata. Every model in the engine follows the same
shape: ``schema_version``, stable ``job_id``, timestamps, a ``status`` (serialized
``State`` value), and a JSON round-trippable ``to_dict`` / ``from_dict``.
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from app.student_recognition.common.timeutil import now_iso

SCHEMA_VERSION = 1


@dataclass
class ArtifactManifest:
    """JSON-serializable metadata for a capture job. No base64 images."""

    job_id: str
    source: str = "browser"
    status: str = ""  # serialized State value (str)
    sha256: str = ""
    created_at: str = ""
    updated_at: str = ""
    schema_version: int = SCHEMA_VERSION
    files: Dict[str, str] = field(default_factory=dict)  # logical name -> rel path
    meta: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "job_id": self.job_id,
            "source": self.source,
            "status": self.status,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "files": dict(self.files),
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArtifactManifest":
        return cls(
            job_id=d["job_id"],
            source=d.get("source", "browser"),
            status=d.get("status", ""),
            sha256=d.get("sha256", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
            files=dict(d.get("files", {})),
            meta=dict(d.get("meta", {})),
        )
