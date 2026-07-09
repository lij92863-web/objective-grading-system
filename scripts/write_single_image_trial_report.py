#!/usr/bin/env python3
"""Write or print a safe single-image trial report."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.single_image_dry_run import run_single_image_dry_run
from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.single_image_trial_report import build_single_image_trial_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--roi", required=True)
    parser.add_argument("--output", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    manifest = load_single_image_manifest(args.manifest)
    report = build_single_image_trial_report(run_single_image_dry_run(args.manifest, args.roi), manifest.image_id)
    output = report.to_safe_dict()
    blockers = report.validate()
    if blockers:
        output["blockers"] = output.get("blockers", []) + blockers
    if args.output:
        output_path = Path(args.output)
        if "data/tmp" not in output_path.as_posix().replace("\\", "/"):
            print(json.dumps({"valid": False, "blockers": ["OUTPUT_MUST_BE_UNDER_DATA_TMP"]}, indent=2), file=sys.stderr)
            return 1
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
