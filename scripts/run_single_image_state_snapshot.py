#!/usr/bin/env python3
"""Build a safe single-image state snapshot."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.manual_roi_schema import load_manual_roi_file, validate_manual_roi_file
from app.recognition.single_image_dry_run import run_single_image_dry_run
from app.recognition.single_image_manifest import load_single_image_manifest, validate_single_image_manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--roi", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    manifest = load_single_image_manifest(args.manifest)
    roi_file = load_manual_roi_file(args.roi)
    dry_run = run_single_image_dry_run(args.manifest, args.roi)
    output = {
        "snapshot_type": "single_image_trial",
        "manifest_summary": validate_single_image_manifest(manifest)["manifest_summary"],
        "roi_summary": validate_manual_roi_file(roi_file)["roi_summary"],
        "dry_run_summary": dry_run.get("snapshot_summary", {}),
        "readiness_summary": {
            "ready_for_qwen_check_only": dry_run.get("ready_for_qwen_check_only", False),
            "ready_for_real_api": False,
        },
        "blockers": dry_run.get("blockers", []),
        "warnings": dry_run.get("warnings", []),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if dry_run.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
