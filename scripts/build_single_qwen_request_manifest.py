#!/usr/bin/env python3
"""Build a Single Qwen Request Manifest from manifest + ROI.

Default: check-only, real_api_allowed=false.
Does NOT call Qwen, read .env, output API keys, or output base64.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.recognition.single_image_manifest import load_single_image_manifest, validate_single_image_manifest
from app.recognition.manual_roi_schema import load_manual_roi_file, validate_manual_roi_file
from app.recognition.qwen_adapter.single_request_manifest import (
    build_request_manifest,
    validate_request_manifest,
    safe_request_manifest_summary,
)
from app.recognition.qwen_adapter.single_prompt_builder import build_single_qwen_prompt


def main():
    parser = argparse.ArgumentParser(description="Build a Single Qwen Request Manifest")
    parser.add_argument("--manifest", required=True, help="Path to single image manifest JSON")
    parser.add_argument("--roi", required=True, help="Path to manual ROI JSON")
    parser.add_argument("--check-only", action="store_true", default=True, help="Check-only mode (default)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--api-key-env", default="", help="Env var name for API key (NOT the key value)")
    args = parser.parse_args()

    manifest = load_single_image_manifest(args.manifest)
    roi_file = load_manual_roi_file(args.roi)

    manifest_result = validate_single_image_manifest(manifest)
    roi_result = validate_manual_roi_file(roi_file)

    req_manifest = build_request_manifest(
        manifest, roi_file,
        check_only=args.check_only,
        api_key_env=args.api_key_env,
    )

    prompt_result = build_single_qwen_prompt(manifest, roi_file)
    manifest_validation = validate_request_manifest(req_manifest)

    output = {
        "request_manifest": safe_request_manifest_summary(req_manifest),
        "prompt_summary": prompt_result.get("summary", {}),
        "blockers": (manifest_result.get("blockers", []) +
                     roi_result.get("blockers", []) +
                     manifest_validation.get("blockers", [])),
        "warnings": (manifest_result.get("warnings", []) +
                     roi_result.get("warnings", []) +
                     manifest_validation.get("warnings", []) +
                     prompt_result.get("warnings", [])),
        "real_api_allowed": False,
        "qwen_called": False,
        "env_read": False,
    }

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("Request Manifest:")
        print(json.dumps(safe_request_manifest_summary(req_manifest), ensure_ascii=False, indent=2))
        if output["blockers"]:
            print(f"\nBlockers: {output['blockers']}")
        if output["warnings"]:
            print(f"Warnings: {output['warnings']}")

    has_blockers = bool(output["blockers"])
    sys.exit(1 if has_blockers else 0)


if __name__ == "__main__":
    main()
