"""Single anonymous image dry-run pipeline without image recognition or Qwen calls."""
from dataclasses import dataclass, field
from typing import Any, Dict

from .manual_roi_schema import load_manual_roi_file
from .single_image_manifest import load_single_image_manifest
from .single_image_trial_context import build_single_image_trial_context


def run_single_image_dry_run(manifest_path: str, roi_path: str) -> dict:
    try:
        manifest = load_single_image_manifest(manifest_path)
        roi_file = load_manual_roi_file(roi_path)
    except Exception as exc:
        return {"valid": False, "blockers": [f"LOAD_FAILED:{exc}"], "warnings": []}
    context = build_single_image_trial_context(manifest, roi_file)
    if context.blockers:
        return {
            "valid": False,
            "ready_for_qwen_check_only": False,
            "ready_for_real_api": False,
            "blockers": context.blockers,
            "warnings": context.warnings,
        }
    review_summary = {"total": 0, "pending": 0, "blocking": 0, "resolved": 0, "by_type": {}}
    teacher_summary = {
        "image_id": manifest.image_id,
        "total_items": context.question_count,
        "needs_review_items": 0,
        "blocking_items": 0,
        "ready_for_review": True,
    }
    snapshot_summary = {
        "snapshot_type": "single_image_trial",
        "image_id": manifest.image_id,
        "roi_count": context.roi_count,
        "real_api_called": False,
    }
    return {
        "valid": True,
        "ready_for_qwen_check_only": context.ready_for_qwen_check_only,
        "ready_for_real_api": False,
        "blockers": [],
        "warnings": context.warnings,
        "review_summary": review_summary,
        "teacher_summary": teacher_summary,
        "snapshot_summary": snapshot_summary,
        "qwen_called": False,
        "grade_all_called": False,
        "formal_report_generated": False,
    }
