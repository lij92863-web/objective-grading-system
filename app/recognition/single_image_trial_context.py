"""Build readiness context for a single anonymous image trial."""
from dataclasses import asdict, dataclass, field
from typing import List

from .manual_roi_schema import ManualROIFile, validate_manual_roi_file
from .single_image_manifest import SingleImageManifest, validate_single_image_manifest


@dataclass
class SingleImageTrialContext:
    image_id: str = ""
    image_sha256: str = ""
    template_id: str = ""
    roi_count: int = 0
    identity_roi_present: bool = False
    question_count: int = 0
    choice_question_count: int = 0
    blank_question_count: int = 0
    ready_for_qwen_check_only: bool = False
    ready_for_real_api: bool = False
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def build_single_image_trial_context(
    manifest: SingleImageManifest | None,
    roi_file: ManualROIFile | None,
    allow_real_api: bool = False,
    api_key_present: bool = False,
) -> SingleImageTrialContext:
    blockers: List[str] = []
    warnings: List[str] = []
    if manifest is None:
        blockers.append("MISSING_MANIFEST")
    if roi_file is None:
        blockers.append("MISSING_ROI_FILE")
    manifest_result = validate_single_image_manifest(manifest) if manifest else {"blockers": [], "warnings": []}
    roi_result = validate_manual_roi_file(roi_file) if roi_file else {"blockers": [], "warnings": []}
    blockers.extend(manifest_result["blockers"])
    blockers.extend(roi_result["blockers"])
    warnings.extend(manifest_result["warnings"])
    warnings.extend(roi_result["warnings"])
    identity_present = bool(roi_file and roi_file.identity_rois)
    if roi_file and not identity_present and "MISSING_IDENTITY_ROI" not in blockers:
        blockers.append("MISSING_IDENTITY_ROI")
    ready_check_only = not blockers
    ready_real_api = bool(ready_check_only and allow_real_api and api_key_present)
    if allow_real_api:
        blockers.append("REAL_API_NOT_ALLOWED_IN_THIS_STAGE")
        ready_real_api = False
    return SingleImageTrialContext(
        image_id=manifest.image_id if manifest else "",
        image_sha256=manifest.image_sha256 if manifest else "",
        template_id=manifest.template_id if manifest else "",
        roi_count=len(roi_file.all_rois()) if roi_file else 0,
        identity_roi_present=identity_present,
        question_count=(len(roi_file.question_rois) + len(roi_file.choice_cell_rois) + len(roi_file.blank_rois)) if roi_file else 0,
        choice_question_count=len({roi.question_id for roi in roi_file.choice_cell_rois}) if roi_file else 0,
        blank_question_count=len(roi_file.blank_rois) if roi_file else 0,
        ready_for_qwen_check_only=ready_check_only,
        ready_for_real_api=ready_real_api,
        blockers=blockers,
        warnings=warnings,
    )
