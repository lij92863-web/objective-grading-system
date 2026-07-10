"""SRE945 Template Builder & Calibration -- template protocol package (v2).

Public surface for the normalized template protocol: the frozen
:class:`TemplateProfile`, its editable :class:`TemplateDraft`, the
:class:`TemplateValidator`, the synthetic (v1) compatibility adapter, the
versioned :class:`TemplateStore`, and coordinate helpers.

This package deliberately contains **no** OMR / image / grading / web_app logic
(constitution B10 / §13). Consumers (OMR / SRE221) must use the frozen accessors
on :class:`TemplateProfile` and never recompute coordinates.
"""

from app.student_recognition.template.anchor_layout import (
    ANCHOR_MODE_FOUR_CORNER,
    ANCHOR_MODE_GRID_ORIGIN,
    CORNER_IDS,
    AnchorError,
    expand_block,
    parse_question_range,
)
from app.student_recognition.template.compatibility import adapt_synthetic_to_v2
from app.student_recognition.template.coordinates import (
    Number,
    clamp_norm,
    in_normalized_bounds,
    is_finite_number,
    to_runtime_pixel_point,
    to_runtime_pixels,
)
from app.student_recognition.template.template_draft import TemplateDraft
from app.student_recognition.template.template_profile import (
    OptionCell,
    SCHEMA_VERSION,
    TemplateProfile,
    TemplateRef,
    _COORDINATE_SYSTEM,
    _IDENTITY_KEYS,
    deep_copy_page,
    union_roi,
    valid_coordinate_system,
)
from app.student_recognition.template.template_store import (
    DEFAULT_TEMPLATES_DIR,
    TemplateStore,
    TemplateStoreError,
)
from app.student_recognition.template.template_validator import (
    TemplateValidationError,
    TemplateValidator,
    ValidationIssue,
    ValidationReport,
)

__all__ = [
    "SCHEMA_VERSION",
    "OptionCell",
    "TemplateRef",
    "TemplateProfile",
    "TemplateDraft",
    "TemplateValidator",
    "TemplateValidationError",
    "ValidationIssue",
    "ValidationReport",
    "TemplateStore",
    "TemplateStoreError",
    "DEFAULT_TEMPLATES_DIR",
    "adapt_synthetic_to_v2",
    "ANCHOR_MODE_GRID_ORIGIN",
    "ANCHOR_MODE_FOUR_CORNER",
    "CORNER_IDS",
    "AnchorError",
    "expand_block",
    "parse_question_range",
    "to_runtime_pixels",
    "to_runtime_pixel_point",
    "in_normalized_bounds",
    "clamp_norm",
    "is_finite_number",
    "Number",
    "_COORDINATE_SYSTEM",
    "_IDENTITY_KEYS",
    "valid_coordinate_system",
    "union_roi",
    "deep_copy_page",
]
