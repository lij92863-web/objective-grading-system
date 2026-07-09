"""Atomic file writes: write to a temp file then ``os.replace`` into place.

Guarantees that a crash mid-write never leaves a half-written artifact (the
constitution's crash-recovery/idempotency requirement, §6). All persistent
writes in the engine must go through these helpers.
"""

import json
import os
import tempfile
from pathlib import Path


def _write_via_temp(path: Path, write_bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=".tmp_", suffix=".part"
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            write_bytes(fh)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    os.replace(tmp, str(path))


def atomic_write_bytes(path, data: bytes) -> None:
    def _w(fh):
        fh.write(data)

    _write_via_temp(path, _w)


def atomic_write_text(path, text: str, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path, obj, encoding: str = "utf-8") -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2), encoding)


def atomic_append_line(path, line: str, encoding: str = "utf-8") -> None:
    """Append a single line atomically (used for ``events.jsonl`` event sourcing)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=".tmp_", suffix=".part"
    )
    try:
        with os.fdopen(fd, "ab") as fh:
            # Preserve any existing content by copying it first.
            if path.exists():
                with open(path, "rb") as existing:
                    fh.write(existing.read())
            fh.write((line + "\n").encode(encoding))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    os.replace(tmp, str(path))
