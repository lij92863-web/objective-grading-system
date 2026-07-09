#!/usr/bin/env python3
"""Check single-image Qwen readiness in check-only mode."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.single_image_trial_context import build_single_image_trial_context


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--roi", required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.check_only:
        result = {"valid": False, "real_api_allowed": False, "blockers": ["CHECK_ONLY_REQUIRED"], "warnings": []}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1
    try:
        context = build_single_image_trial_context(
            load_single_image_manifest(args.manifest),
            load_manual_roi_file(args.roi),
        )
        result = context.to_dict()
        result["valid"] = context.ready_for_qwen_check_only
        result["real_api_allowed"] = False
        result["api_key_required"] = False
        result["real_api_called"] = False
    except Exception as exc:
        result = {"valid": False, "real_api_allowed": False, "blockers": [f"LOAD_FAILED:{exc}"], "warnings": []}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
