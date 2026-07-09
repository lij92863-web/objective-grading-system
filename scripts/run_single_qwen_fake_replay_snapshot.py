#!/usr/bin/env python3
"""Run a state snapshot for a single Qwen fake replay.

Combines the fake replay + snapshot into one command.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.qwen_adapter.single_fake_replay import run_single_fake_replay


def main():
    parser = argparse.ArgumentParser(description="Single Qwen Fake Replay Snapshot")
    parser.add_argument("--manifest", required=True, help="Path to single image manifest JSON")
    parser.add_argument("--roi", required=True, help="Path to manual ROI JSON")
    parser.add_argument("--fake-response", required=True, help="Path to fake Qwen response fixture")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    manifest = load_single_image_manifest(args.manifest)
    roi_file = load_manual_roi_file(args.roi)

    with open(args.fake_response, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        fake_payload = json.loads(content)
    except json.JSONDecodeError:
        fake_payload = {"_malformed_raw": content, "items": []}

    replay_result = run_single_fake_replay(manifest, roi_file, fake_payload)

    snapshot = {
        "snapshot_type": "single_qwen_fake_replay",
        "request_manifest_summary": replay_result.get("request_manifest", {}),
        "sanitized_summary": replay_result.get("sanitized_summary", {}),
        "parser_audit_summary": replay_result.get("parser_audit", {}),
        "review_summary": replay_result.get("review_summary", {}),
        "teacher_summary": replay_result.get("teacher_summary", {}),
        "trial_report_summary": replay_result.get("trial_report", {}),
        "real_api_called": False,
        "qwen_called": False,
        "grade_all_called": False,
        "formal_report_generated": False,
    }

    if args.json:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    else:
        print(f"Snapshot type: {snapshot['snapshot_type']}")
        audit = snapshot.get("parser_audit_summary", {})
        print(f"Candidates: {audit.get('candidate_count', 0)}, "
              f"valid: {audit.get('valid_candidate_count', 0)}, "
              f"need review: {audit.get('review_candidate_count', 0)}")
        print(f"real_api_called: {snapshot['real_api_called']}")

    sys.exit(0)


if __name__ == "__main__":
    main()
