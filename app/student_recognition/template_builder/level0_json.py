"""SRE945 Level-0 (pure JSON) template IO / validation entry point.

A hand-authored or script-generated ``template_profile.json`` can be directly
validated and promoted to a frozen :class:`TemplateProfile` through this module,
with no calibration UI required. All IO is atomic and stdlib-only.
"""

import json
from pathlib import Path
from typing import Any, Dict, Union

from app.student_recognition.common.atomic_io import atomic_write_json
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template.template_validator import (
    TemplateValidationError,
    TemplateValidator,
    ValidationReport,
)

__all__ = [
    "load_template_json",
    "validate_template_json",
    "validate_template_dict",
    "build_profile_from_json",
    "read_validated_template",
    "save_template_json",
]


def load_template_json(path: Union[str, Path]) -> Dict[str, Any]:
    """Read a template JSON file into a dict (raises on malformed JSON)."""
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _as_dict(source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    """Return a dict from either a dict or a path to a JSON file."""
    if isinstance(source, dict):
        return source
    return load_template_json(source)


def validate_template_json(
    source: Union[str, Path, Dict[str, Any]]
) -> ValidationReport:
    """Validate a template JSON file or dict; return the :class:`ValidationReport`."""
    data = _as_dict(source)
    profile = TemplateProfile.from_dict(data)
    return TemplateValidator().validate(profile)


def validate_template_dict(data: Dict[str, Any]) -> ValidationReport:
    """Validate a template *dict*; raise :class:`TemplateValidationError` if invalid.

    Every finding carries a constitutional :class:`ErrorCode` (constitution B6).
    """
    profile = TemplateProfile.from_dict(data)
    report = TemplateValidator().validate(profile)
    if report.status != "valid":
        raise TemplateValidationError(report)
    return report


def build_profile_from_json(
    source: Union[str, Path, Dict[str, Any]]
) -> TemplateProfile:
    """Validate-and-build a :class:`TemplateProfile` from a JSON file or dict."""
    data = _as_dict(source)
    return TemplateProfile.from_dict(data)


def read_validated_template(
    source: Union[str, Path, Dict[str, Any]]
) -> TemplateProfile:
    """Build a validated :class:`TemplateProfile` from a JSON file or dict.

    Raises:
        TemplateValidationError: If the template fails validation.
    """
    data = _as_dict(source)
    profile = TemplateProfile.from_dict(data)
    report = TemplateValidator().validate(profile)
    if report.status != "valid":
        raise TemplateValidationError(report)
    return profile


def save_template_json(
    path: Union[str, Path], profile_or_dict: Union[TemplateProfile, Dict[str, Any]]
) -> None:
    """Atomically write a template profile (or dict) as JSON."""
    payload = (
        profile_or_dict.to_dict()
        if isinstance(profile_or_dict, TemplateProfile)
        else profile_or_dict
    )
    atomic_write_json(Path(path), payload)
