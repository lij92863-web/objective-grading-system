#!/usr/bin/env python3
"""Single-image, single-prompt Qwen smoke test — **default dry-run**.

Usage (dry-run — no API call)::

    python scripts/qwen_single_image_smoke.py --image path/to/crop.png --prompt-type choice_cell

Usage (real call — requires env vars)::

    python scripts/qwen_single_image_smoke.py --image path/to/crop.png --prompt-type choice_cell --no-dry-run

For ``complex_blank_judgment``::

    python scripts/qwen_single_image_smoke.py --image ... --prompt-type complex_blank_judgment \
        --standard-answer "x>1" --student-answer "(1,+inf)"

Safety: never prints API key or base64 image data.
"""

import argparse
import os
import sys

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VALID_PROMPT_TYPES = {"name_field", "choice_cell", "blank_answer", "complex_blank_judgment"}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Single-image Qwen API smoke test (default dry-run)."
    )
    p.add_argument("--image", required=True, help="Path to a cropped image file.")
    p.add_argument(
        "--prompt-type",
        required=True,
        choices=sorted(VALID_PROMPT_TYPES),
        help="Prompt type.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Build request but do not send (default).",
    )
    p.add_argument(
        "--no-dry-run",
        action="store_true",
        default=False,
        help="Actually call the Qwen API (requires QWEN_API_ENABLED=true, etc.).",
    )
    p.add_argument("--standard-answer", default="", help="For complex_blank_judgment.")
    p.add_argument("--student-answer", default="", help="For complex_blank_judgment.")
    p.add_argument("--question-text", default="", help="For complex_blank_judgment.")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    # -- validate inputs --------------------------------------------------------
    image_path = Path(args.image)
    if not image_path.exists() or not image_path.is_file():
        print(f"[ERROR] Image not found: {args.image}", file=sys.stderr)
        return 1

    do_real_call = args.no_dry_run

    # -- import adapter (late, so --help is fast) --------------------------------
    from app.recognition.qwen_adapter import (
        FakeQwenClient,
        QwenAdapterError,
        QwenRequest,
        RealQwenClient,
    )
    from app.recognition.qwen_adapter.prompt_builder import build_prompt
    from app.recognition.qwen_adapter.parser import parse_qwen_response

    # -- build request ----------------------------------------------------------
    metadata = {}
    if args.prompt_type == "complex_blank_judgment":
        if not args.standard_answer or not args.student_answer:
            print(
                "[ERROR] complex_blank_judgment requires --standard-answer and --student-answer.",
                file=sys.stderr,
            )
            return 1
        metadata = {
            "standard_answer": args.standard_answer,
            "student_answer": args.student_answer,
            "question_text": args.question_text,
            "points": "",
            "ocr_confidence": "",
            "format_required": "否",
        }

    from app.recognition.qwen_adapter.models import QwenImageInput

    image_input = QwenImageInput(
        image_id="smoke_001",
        image_path=str(image_path.resolve()),
        mime_type="image/jpeg",
        prompt_type=args.prompt_type,
    )

    request = QwenRequest(
        prompt_type=args.prompt_type,
        prompt="",
        image=image_input,
        metadata=metadata,
    )
    request_id = request.request_id

    prompt = build_prompt(request)

    # -- dry-run ----------------------------------------------------------------
    if not do_real_call:
        print("=== DRY-RUN (no API call) ===")
        print(f"  request_id      : {request_id}")
        print(f"  prompt_type     : {args.prompt_type}")
        print(f"  image           : {image_path}")
        print(f"  image_base64    : <not loaded in dry-run>")
        if metadata:
            print(f"  standard_answer : {metadata.get('standard_answer', '')}")
            print(f"  student_answer  : {metadata.get('student_answer', '')}")
        print(f"  prompt length   : {len(prompt)} chars")
        print("  [OK] dry-run complete — request was NOT sent.")
        return 0

    # -- real call --------------------------------------------------------------
    print("=== REAL QWEN API CALL ===")
    print(f"  request_id      : {request_id}")
    print(f"  prompt_type     : {args.prompt_type}")
    print(f"  image           : {image_path}")
    print(f"  image_base64    : <base64 omitted>")
    print(f"  QWEN_API_ENABLED: {os.environ.get('QWEN_API_ENABLED', '')}")
    print()

    try:
        client = RealQwenClient()
        if args.prompt_type == "name_field":
            resp = client.recognize_name_field(request)
        elif args.prompt_type == "choice_cell":
            resp = client.recognize_choice_cell(request)
        elif args.prompt_type == "blank_answer":
            resp = client.recognize_blank_answer(request)
        else:
            resp = client.judge_complex_blank(request)
    except QwenAdapterError as exc:
        print(f"[ERROR] {exc.code}: {exc.message}")
        return 2

    result = parse_qwen_response(resp, args.prompt_type, request_id=request_id)
    print(f"  parsed status   : {result.status}")
    print(f"  errors          : {result.errors}")
    print(f"  warnings        : {result.warnings}")
    print(f"  confidence      : {result.confidence}")
    if result.status == "ok":
        print("  [OK] response parsed successfully.")
    else:
        print("  [WARN] response has errors — check above.")
    return 0 if result.status == "ok" else 3


if __name__ == "__main__":
    raise SystemExit(main())
