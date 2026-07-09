"""Path safety: every artifact must live under ``data/captures/jobs/<id>/``.

This module is the *only* place that knows the on-disk persistence tree. It
defends against path traversal and enforces the fixed layout required by the
constitution (§4). Business modules must obtain their paths from here rather
than constructing them ad-hoc.

The captures root is overridable (used by tests); production code uses the
default ``<project>/data/captures``.
"""

import os
import re
from pathlib import Path

# Project root = parents[3] from this file:
#   common/safe_paths.py -> student_recognition -> app -> <project root>
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CAPTURES_ROOT = _PROJECT_ROOT / "data" / "captures"

_CAPTURES_ROOT = _DEFAULT_CAPTURES_ROOT
JOBS_DIRNAME = "jobs"

_JOB_ID_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")
_REL_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")


def set_captures_root(path) -> None:
    """Override the captures root (tests use a temp directory)."""
    global _CAPTURES_ROOT
    _CAPTURES_ROOT = Path(path)


def reset_captures_root() -> None:
    """Restore the default captures root."""
    global _CAPTURES_ROOT
    _CAPTURES_ROOT = _DEFAULT_CAPTURES_ROOT


def captures_root() -> Path:
    return _CAPTURES_ROOT


def sha256_index_path(root=None) -> Path:
    """Path of the sha256 -> job_id dedup index (a meta file, not an artifact)."""
    base = Path(root) if root is not None else _CAPTURES_ROOT
    return base / "sha256_index.json"


def validate_job_id(job_id: str) -> None:
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job_id must be a non-empty string")
    if "/" in job_id or "\\" in job_id or ".." in job_id:
        raise ValueError(f"invalid job_id (path traversal): {job_id!r}")
    if not _JOB_ID_RE.match(job_id):
        raise ValueError(f"invalid job_id charset: {job_id!r}")


def validate_rel(name: str) -> None:
    if not isinstance(name, str) or name in ("", ".", ".."):
        raise ValueError(f"invalid relative name: {name!r}")
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError(f"invalid relative name (path traversal): {name!r}")
    if not _REL_RE.match(name):
        raise ValueError(f"invalid relative name charset: {name!r}")


def job_dir(job_id: str) -> Path:
    """Return the fixed artifact directory for ``job_id`` (created callers' job)."""
    validate_job_id(job_id)
    return _CAPTURES_ROOT / JOBS_DIRNAME / job_id


def job_subdir(job_id: str, name: str) -> Path:
    """Return a validated sub-directory (e.g. ``normalized``, ``crops``)."""
    validate_rel(name)
    return job_dir(job_id) / name


def safe_join(base, *parts) -> Path:
    """Join ``parts`` under ``base`` and guarantee the result stays within ``base``."""
    base = Path(base).resolve()
    result = base
    for part in parts:
        validate_rel(str(part))
        result = result / str(part)
    result = result.resolve()
    if result != base and base not in result.parents:
        raise ValueError("path escapes base directory")
    return result


def ensure_dir(path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
