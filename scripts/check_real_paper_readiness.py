#!/usr/bin/env python3
"""R141: Real paper readiness CLI."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.real_paper_readiness_gate import check_readiness


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--has-anonymous-image", action="store_true")
    p.add_argument("--has-template", action="store_true")
    p.add_argument("--has-manual-roi", action="store_true")
    p.add_argument("--qwen-check-only-passed", action="store_true")
    p.add_argument("--qwen-api-key-present", action="store_true")
    args = p.parse_args()
    result = check_readiness(has_anonymous_image=args.has_anonymous_image,
                              has_template=args.has_template or True,
                              has_manual_roi=args.has_manual_roi,
                              qwen_check_only_passed=args.qwen_check_only_passed,
                              qwen_api_key_present=args.qwen_api_key_present)
    print(json.dumps({"ready_for_single_real_qwen_trial": result.ready_for_single_real_qwen_trial,
                      "ready_for_three_image_trial": result.ready_for_three_image_trial,
                      "ready_for_small_batch_trial": result.ready_for_small_batch_trial,
                      "blockers": result.blockers}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
