"""TemplateDraft -- the editable, pre-validation template (SRE945-B).

A ``TemplateDraft`` is mutable and may be incomplete. It can only become a
frozen :class:`~app.student_recognition.template.template_profile.TemplateProfile`
(after passing :class:`TemplateValidator`). Until then it MUST NOT be used by
downstream consumers (OMR / ImageNorm): attempting to read recognition data from
a draft raises ``TemplateValidationError(TEMPLATE_DRAFT_NOT_FINALIZED)``.
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.errors.error_message import message_for
from app.student_recognition.template.template_profile import (
    SCHEMA_VERSION,
    _COORDINATE_SYSTEM,
    TemplateProfile,
)
from app.student_recognition.template.template_validator import (
    TemplateValidationError,
    ValidationIssue,
    ValidationReport,
    TemplateValidator,
)

__all__ = ["TemplateDraft"]


@dataclass
class TemplateDraft:
    """Editable, possibly-incomplete template definition."""

    template_id: Optional[str] = None
    template_name: Optional[str] = None
    template_version: int = 1
    reference_canvas: Dict[str, Any] = field(default_factory=dict)
    pages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Builder helpers
    # ------------------------------------------------------------------ #
    def add_page(
        self,
        template_page_id: str,
        page_no: int,
        anchors: Optional[List[Dict[str, Any]]] = None,
        identity: Optional[Dict[str, Any]] = None,
        question_blocks: Optional[List[Dict[str, Any]]] = None,
        blank_rois: Optional[List[Dict[str, Any]]] = None,
    ) -> "TemplateDraft":
        """Append a page descriptor and return ``self`` for chaining."""
        self.pages.append(
            {
                "template_page_id": template_page_id,
                "page_no": page_no,
                "anchors": list(anchors or []),
                "identity": dict(identity or {}),
                "question_blocks": list(question_blocks or []),
                "blank_rois": list(blank_rois or []),
            }
        )
        return self

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "template_version": self.template_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "coordinate_system": dict(_COORDINATE_SYSTEM),
            "reference_canvas": dict(self.reference_canvas),
            "pages": [copy.deepcopy(p) for p in self.pages],
        }

    # ------------------------------------------------------------------ #
    # Finalization
    # ------------------------------------------------------------------ #
    def finalize(self) -> TemplateProfile:
        """Validate this draft and promote it to a frozen ``TemplateProfile``.

        Raises:
            TemplateValidationError: If validation fails (report carries the
                constitutional ``ErrorCode`` members).
        """
        profile = TemplateProfile.from_dict(self.to_dict())
        report = TemplateValidator().validate(profile)
        if report.status != "valid":
            raise TemplateValidationError(report)
        return profile

    # ------------------------------------------------------------------ #
    # Anti-pattern guard: drafts must not be used for recognition
    # ------------------------------------------------------------------ #
    def get_option_cells(self, question_no: int) -> None:  # pragma: no cover - guard
        """Draft has no consumer interface; raises until finalized."""
        raise TemplateValidationError(
            ValidationReport.invalid(
                [
                    ValidationIssue(
                        ErrorCode.TEMPLATE_DRAFT_NOT_FINALIZED,
                        message_for(ErrorCode.TEMPLATE_DRAFT_NOT_FINALIZED),
                        "TemplateDraft.get_option_cells",
                    )
                ]
            )
        )
