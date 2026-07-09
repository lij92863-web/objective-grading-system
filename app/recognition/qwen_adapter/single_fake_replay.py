"""Single Qwen Fake Replay Pipeline — fake response → sanitizer → parser → audit → review → trial report.

Does NOT call real API. Does NOT read .env. Does NOT save raw response.
Does NOT output base64. Does NOT enter grade_all. Does NOT generate formal reports.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .single_sanitized_output import SingleQwenSanitizedOutput
from .single_sanitizer import sanitize_single_qwen_response
from .single_response_parser import parse_single_qwen_response
from .parser_candidate_audit import audit_parser_candidates, ParserCandidateAudit
from .single_request_manifest import (
    build_request_manifest,
    SingleQwenRequestManifest,
)


def run_single_fake_replay(
    manifest: Any,
    roi_file: Any,
    fake_response_payload: dict,
    request_id: str = "",
) -> Dict[str, Any]:
    """Run full fake replay pipeline.

    Chain: request manifest → sanitizer → parser → parser audit → summary.
    """
    if not request_id:
        import uuid
        request_id = uuid.uuid4().hex[:12]

    # 1. Build request manifest
    req_manifest = build_request_manifest(manifest, roi_file, check_only=True)

    # 2. Sanitize
    sanitized = sanitize_single_qwen_response(
        fake_response_payload,
        request_id=request_id,
        image_sha256=req_manifest.image_sha256,
        engine_name="fake-qwen",
        real_api_called=False,
    )

    # 3. Parse
    parsed = parse_single_qwen_response(sanitized, roi_file)

    # 4. Audit
    audit = audit_parser_candidates(parsed, sanitized, request_id=request_id)

    # 5. Build review queue summary (in-memory, no file writes)
    review_summary = _build_review_summary(parsed, audit)

    # 6. Build teacher summary
    teacher_summary = _build_teacher_summary(parsed, audit, sanitized)

    # 7. Build trial report
    trial_report = _build_trial_report(req_manifest, sanitized, audit)

    return {
        "ok": True,
        "real_api_called": False,
        "qwen_called": False,
        "grade_all_called": False,
        "formal_report_generated": False,
        "request_manifest": req_manifest.to_dict(),
        "sanitized_summary": {
            "engine_status": sanitized.engine_status,
            "candidate_count": sanitized.candidate_count,
            "identity_candidate_present": sanitized.identity_candidate is not None,
            "exception_codes": sanitized.exception_codes,
            "warnings": sanitized.warnings,
        },
        "parser_audit": audit.to_dict(),
        "review_summary": review_summary,
        "teacher_summary": teacher_summary,
        "trial_report": trial_report,
    }


def _build_review_summary(parsed: dict, audit: ParserCandidateAudit) -> dict:
    candidates = parsed.get("parsed_candidates", [])
    review_items = [c for c in candidates if c.get("needs_review")]
    return {
        "total_items": len(candidates),
        "needs_review_items": len(review_items),
        "blocking_items": audit.blocking_candidate_count,
        "invalid_options": audit.invalid_option_count,
        "identity_review_required": audit.identity_candidate_count > 0,
        "ready_for_review": audit.ready_for_review_queue,
        "ready_for_grading": False,
    }


def _build_teacher_summary(parsed: dict, audit: ParserCandidateAudit, sanitized: SingleQwenSanitizedOutput) -> dict:
    return {
        "total_items": len(parsed.get("parsed_candidates", [])),
        "auto_accepted": audit.valid_candidate_count,
        "needs_review": audit.review_candidate_count,
        "blocking": audit.blocking_candidate_count,
        "identity_candidate": audit.identity_candidate_count,
        "engine_status": sanitized.engine_status,
        "real_api_called": False,
    }


def _build_trial_report(req_manifest: SingleQwenRequestManifest, sanitized: SingleQwenSanitizedOutput, audit: ParserCandidateAudit) -> dict:
    return {
        "report_version": 1,
        "request_id": req_manifest.request_id,
        "image_id": req_manifest.image_id,
        "manifest_valid": req_manifest.manifest_valid,
        "roi_valid": req_manifest.roi_valid,
        "real_api_called": False,
        "raw_response_saved": False,
        "base64_emitted": False,
        "engine_status": sanitized.engine_status,
        "ready_for_review_queue": audit.ready_for_review_queue,
        "ready_for_real_api": False,
        "ready_for_grading": False,
        "next_step": "manual review of fake replay results; do not start batch",
    }
