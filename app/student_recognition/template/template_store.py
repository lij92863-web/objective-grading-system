"""SRE945 TemplateStore -- versioned persistence of TemplateProfile (v2).

Templates are stored as atomic JSON files named ``{template_id}_v{version}.json``
under a templates directory. Versioning is strict: a given ``(template_id,
template_version)`` is **immutable** -- re-saving it raises
:class:`TemplateStoreError` (ErrorCode TEMPLATE_VERSION_CONFLICT) so an older
version is never silently overwritten (SRE945 design §8).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from app.student_recognition.common.atomic_io import atomic_write_json
from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.template_profile import TemplateProfile

__all__ = [
    "TemplateStoreError",
    "TemplateStore",
    "DEFAULT_TEMPLATES_DIR",
]

logger = logging.getLogger(__name__)

# Default location of committed template fixtures (relative to project root).
# __file__ = .../app/student_recognition/template/template_store.py
# parents[3] == project root.
DEFAULT_TEMPLATES_DIR = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "student_recognition"
    / "fixtures"
    / "templates"
)


class TemplateStoreError(ValueError):
    """Base error for template-store operations, always tied to an ErrorCode."""

    def __init__(self, error_code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.error_code: ErrorCode = error_code


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _template_filename(template_id: str, version: int) -> str:
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in template_id)
    return f"{safe_id}_v{version}.json"


class TemplateStore:
    """Atomic, versioned storage for :class:`TemplateProfile` artifacts."""

    def __init__(self, directory: "str | Path | None" = None) -> None:
        self.directory: Path = Path(directory) if directory else DEFAULT_TEMPLATES_DIR
        self.directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Save / load
    # ------------------------------------------------------------------ #
    def save(
        self,
        profile: TemplateProfile,
        directory: "str | Path | None" = None,
        overwrite: bool = False,
    ) -> Path:
        """Persist ``profile`` atomically; refuse to overwrite same version.

        Args:
            profile: The validated :class:`TemplateProfile` to persist.
            directory: Optional override for the target directory.
            overwrite: If True, replace an existing ``(id, version)`` file.

        Raises:
            TemplateStoreError: If ``(template_id, template_version)`` already
                exists in the target directory and ``overwrite`` is False.
        """
        target_dir = Path(directory) if directory else self.directory
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / _template_filename(profile.template_id, profile.template_version)

        if path.exists() and not overwrite:
            raise TemplateStoreError(
                ErrorCode.TEMPLATE_VERSION_CONFLICT,
                f"template '{profile.template_id}' v{profile.template_version} "
                f"already exists at {path}; refusing to overwrite "
                f"(set overwrite=True to replace).",
            )

        payload = profile.to_dict()
        if payload.get("created_at") is None:
            payload["created_at"] = _now_iso()
        payload["updated_at"] = _now_iso()

        atomic_write_json(path, payload)
        logger.info("saved template %s v%s -> %s", profile.template_id, profile.template_version, path)
        return path

    def load(self, path: "str | Path") -> TemplateProfile:
        """Load and validate a single template JSON file."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return TemplateProfile.from_dict(data)

    def list_templates(
        self, directory: "str | Path | None" = None
    ) -> List[Tuple[str, str, int]]:
        """List stored templates as ``(path, template_id, template_version)``.

        Corrupt / unparseable JSON files are skipped (and logged) rather than
        raising, so a single bad artifact never breaks enumeration.
        """
        target_dir = Path(directory) if directory else self.directory
        if not target_dir.exists():
            return []
        results: List[Tuple[str, str, int]] = []
        for path in sorted(target_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                tid = str(data.get("template_id", ""))
                tver = int(data.get("template_version", 0))
            except Exception:  # noqa: BLE001 - deliberately broad: skip any bad file
                logger.warning("skipping corrupt/unreadable template file %s", path)
                continue
            results.append((str(path), tid, tver))
        return results
