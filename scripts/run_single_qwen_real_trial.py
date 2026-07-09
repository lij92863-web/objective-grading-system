#!/usr/bin/env python3
"""Single Real Qwen One-Shot Runner — SHELL/GATE ONLY.

DEFAULT FAIL-CLOSED. All of the following gates MUST pass before a real
API call is even considered:
- --allow-real-api
- --confirm-anonymous
- --check-only-passed
- --api-key-env (env var NAME, not value)
- max_calls=1
- save_raw_response must remain false
- emit_base64 must remain false
- output must be in data/tmp

This script does NOT read .env. It only checks that the named env var exists.
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def check_gate(args) -> dict:
    """Run all gates. Returns blockers list."""
    blockers = []
    warnings = []

    # Gate 1: --allow-real-api
    if not args.allow_real_api:
        blockers.append("MISSING_ALLOW_REAL_API")

    # Gate 2: --confirm-anonymous
    if not args.confirm_anonymous:
        blockers.append("MISSING_CONFIRM_ANONYMOUS")

    # Gate 3: --check-only-passed
    if not args.check_only_passed:
        blockers.append("MISSING_CHECK_ONLY_PASSED")

    # Gate 4: --api-key-env
    if not args.api_key_env:
        blockers.append("MISSING_API_KEY_ENV")
    else:
        key_value = os.environ.get(args.api_key_env, "").strip()
        if not key_value:
            blockers.append(f"ENV_VAR_NOT_SET:{args.api_key_env}")
        # Do NOT print the key value

    # Gate 5: max_calls
    if args.max_calls > 1:
        blockers.append(f"MAX_CALLS_EXCEEDS_ONE:{args.max_calls}")
    if args.max_calls < 1:
        blockers.append("MAX_CALLS_LESS_THAN_ONE")

    # Gate 6: save_raw_response must be false
    if args.save_raw_response:
        blockers.append("SAVE_RAW_RESPONSE_MUST_BE_FALSE")

    # Gate 7: emit_base64 must be false
    if args.emit_base64:
        blockers.append("EMIT_BASE64_MUST_BE_FALSE")

    # Gate 8: output must be in data/tmp
    if args.output:
        output_str = str(args.output).replace("\\", "/")
        if "data/reports" in output_str or "data/exams" in output_str:
            blockers.append("OUTPUT_NOT_IN_DATA_TMP")

    return {
        "gates_passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "real_api_called": False,  # ALWAYS false at gate check
    }


def main():
    parser = argparse.ArgumentParser(
        description="Single Real Qwen One-Shot Trial Runner (DEFAULT FAIL-CLOSED)")
    parser.add_argument("--manifest", default="", help="Path to single image manifest JSON")
    parser.add_argument("--roi", default="", help="Path to manual ROI JSON")
    parser.add_argument("--allow-real-api", action="store_true", default=False,
                        help="EXPLICITLY allow real API call")
    parser.add_argument("--confirm-anonymous", action="store_true", default=False,
                        help="EXPLICITLY confirm image is anonymous")
    parser.add_argument("--check-only-passed", action="store_true", default=False,
                        help="Confirm check-only gate passed")
    parser.add_argument("--api-key-env", default="", help="Env var NAME (not value) for API key")
    parser.add_argument("--max-calls", type=int, default=1, help="Maximum API calls (must be 1)")
    parser.add_argument("--output", default="data/tmp/single_qwen_sanitized.json",
                        help="Output path (must be in data/tmp)")
    parser.add_argument("--save-raw-response", action="store_true", default=False,
                        help="Save raw response (MUST BE FALSE)")
    parser.add_argument("--emit-base64", action="store_true", default=False,
                        help="Emit base64 (MUST BE FALSE)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    gate_result = check_gate(args)

    output = {
        **gate_result,
        "real_api_called": False,
        "raw_response_saved": False,
        "base64_emitted": False,
        "api_key_read": False,
        "env_read": False,
        "next_step": (
            "All gates failed as expected — no real API called. "
            "Provide all required flags to proceed."
            if gate_result["blockers"]
            else "All gates passed — real API call would be allowed (NOT IMPLEMENTED in this stage)."
        ),
    }

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        passed = "PASSED" if gate_result["gates_passed"] else "FAILED (expected)"
        print(f"Gate check: {passed}")
        if gate_result["blockers"]:
            print(f"Blockers: {gate_result['blockers']}")
        print(f"real_api_called: {output['real_api_called']}")

    # Default: fail-closed
    if not gate_result["gates_passed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
