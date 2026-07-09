"""R151: Recognition state snapshot — debug-safe, no secrets."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RecognitionStateSnapshot:
    snapshot_id: str = ""
    snapshot_type: str = "batch"
    batch_id: str = ""
    status: str = ""
    batch_summary: Dict[str, Any] = field(default_factory=dict)
    review_summary: Dict[str, Any] = field(default_factory=dict)
    qwen_policy_summary: Dict[str, Any] = field(default_factory=dict)
    teacher_summary: Dict[str, Any] = field(default_factory=dict)
    manifest_summary: Dict[str, Any] = field(default_factory=dict)
    roi_summary: Dict[str, Any] = field(default_factory=dict)
    dry_run_summary: Dict[str, Any] = field(default_factory=dict)
    readiness_summary: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    created_at: str = ""

    def to_safe_dict(self) -> dict:
        """Safe output: no API key, no raw response, no base64, no full paths."""
        return {"snapshot_id": self.snapshot_id, "snapshot_type": self.snapshot_type,
                "batch_id": self.batch_id,
                "status": self.status, "batch_summary": self.batch_summary,
                "review_summary": self.review_summary,
                "qwen_policy_summary": self.qwen_policy_summary,
                "teacher_summary": self.teacher_summary,
                "manifest_summary": self.manifest_summary,
                "roi_summary": self.roi_summary,
                "dry_run_summary": self.dry_run_summary,
                "readiness_summary": self.readiness_summary,
                "warnings": self.warnings, "created_at": self.created_at}
