#!/usr/bin/env python3
"""Run Single Qwen Fake Replay — fake response → sanitizer → parser → audit → summary.

Does NOT call real API. Does NOT read .env. Does NOT generate formal reports.
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


def load_fake_response(path: str) -> dict:
    """Load a fake response payload from JSON file."""
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Malformed JSON — return raw text as a pseudo-payload
        return {"_malformed_raw": content, "items": []}


def main():
    parser = argparse.ArgumentParser(description="Run Single Qwen Fake Replay")
    parser.add_argument("--manifest", required=True, help="Path to single image manifest JSON")
    parser.add_argument("--roi", required=True, help="Path to manual ROI JSON")
    parser.add_argument("--fake-response", required=True, help="Path to fake Qwen response fixture")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    manifest = load_single_image_manifest(args.manifest)
    roi_file = load_manual_roi_file(args.roi)
    fake_payload = load_fake_response(args.fake_response)

    result = run_single_fake_replay(manifest, roi_file, fake_payload)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Fake replay completed: ok={result['ok']}")
        print(f"Engine status: {result.get('sanitized_summary', {}).get('engine_status', 'unknown')}")
        audit = result.get('parser_audit', {})
        print(f"Candidates: {audit.get('candidate_count', 0)} total, "
              f"{audit.get('valid_candidate_count', 0)} valid, "
              f"{audit.get('review_candidate_count', 0)} need review")
        print(f"Ready for review queue: {audit.get('ready_for_review_queue', False)}")
        print(f"Ready for grading: {audit.get('ready_for_grading', False)}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
