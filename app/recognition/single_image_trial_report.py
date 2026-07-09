"""Safe single-image trial report model."""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class SingleImageTrialReport:
    report_version: int = 1
    image_id: str = ""
    manifest_valid: bool = False
    roi_valid: bool = False
    qwen_check_only_passed: bool = False
    real_api_called: bool = False
    raw_response_saved: bool = False
    base64_emitted: bool = False
    ready_for_real_api: bool = False
    dry_run_summary: Dict[str, Any] = field(default_factory=dict)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    next_step: str = "run sanitized single-image check-only review; do not start batch"

    def validate(self) -> List[str]:
        blockers: List[str] = []
        if self.real_api_called:
            blockers.append("REAL_API_CALLED")
        if self.raw_response_saved:
            blockers.append("RAW_RESPONSE_SAVED")
        if self.base64_emitted:
            blockers.append("BASE64_EMITTED")
        if "batch" in self.next_step.lower() and "do not start batch" not in self.next_step.lower():
            blockers.append("NEXT_STEP_DIRECT_BATCH_FORBIDDEN")
        return blockers

    def to_safe_dict(self) -> dict:
        data = asdict(self)
        data["ready_for_real_api"] = False
        data["real_api_called"] = False
        data["raw_response_saved"] = False
        data["base64_emitted"] = False
        return data


def build_single_image_trial_report(dry_run_result: dict, image_id: str = "") -> SingleImageTrialReport:
    blockers = list(dry_run_result.get("blockers", []))
    warnings = list(dry_run_result.get("warnings", []))
    return SingleImageTrialReport(
        image_id=image_id,
        manifest_valid=dry_run_result.get("valid", False),
        roi_valid=dry_run_result.get("valid", False),
        qwen_check_only_passed=dry_run_result.get("ready_for_qwen_check_only", False),
        ready_for_real_api=False,
        dry_run_summary={
            "valid": dry_run_result.get("valid", False),
            "review_summary": dry_run_result.get("review_summary", {}),
            "snapshot_summary": dry_run_result.get("snapshot_summary", {}),
        },
        blockers=blockers,
        warnings=warnings,
    )
