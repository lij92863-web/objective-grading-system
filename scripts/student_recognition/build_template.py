#!/usr/bin/env python3
"""SRE945 template builder CLI.

Renders a mark-free (blank) synthetic answer card and promotes its geometry into
a v2 :class:`TemplateProfile`, persisting:

* ``<out-dir>/template-<id>.json``
* ``<out-dir>/blank-<id>.png`` (synthetic, no real student image -- B5)

Pure stdlib + the engine's template/synthetic modules. It deliberately does NOT
import ``web_app`` / ``flask`` / ``omr`` / ``image`` / ``grading_bridge``
(lockdown; verified by the dependency guard).

Usage:
    python scripts/student_recognition/build_template.py --template-id objective_sheet_v1
"""

import argparse
import sys
from pathlib import Path

# Allow running as a standalone script as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.student_recognition.synthetic.ground_truth import AnswerRecord, GroundTruth
from app.student_recognition.synthetic.generator import SyntheticSheetGenerator
from app.student_recognition.synthetic.template_profile import build_default_template
from app.student_recognition.template_builder.calibrator import Calibrator
from app.student_recognition.template.template_store import DEFAULT_TEMPLATES_DIR
from app.student_recognition.template_builder.level0_json import save_template_json
from app.student_recognition.template.template_validator import TemplateValidationError


def _build_blank_ground_truth(template_id: str, question_count: int) -> GroundTruth:
    """Build a mark-free ground truth (every answer is 'none')."""
    answers = [
        AnswerRecord(
            question=q,
            selected=None,
            mark_type="none",
            expected_option="",
        )
        for q in range(1, question_count + 1)
    ]
    return GroundTruth(
        sheet_id=f"blank-{template_id}",
        template_id=template_id,
        student={"student_id": "", "name": ""},
        answers=answers,
        perturbation="clean",
        seed=0,
    )


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description="Build a v2 normalized template + blank card.")
    parser.add_argument(
        "--template-id",
        default="objective_sheet_v1",
        help="Logical template id (also used for the fixture file names).",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_TEMPLATES_DIR),
        help="Directory to write the template JSON + blank PNG fixtures.",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Synthetic geometry.
    synthetic = build_default_template(
        template_id=args.template_id, template_version=1
    )
    question_count = int(synthetic.bubble_grid["rows"])

    # 2) Render a mark-free (blank) card -- synthetic only, never a real image.
    gt = _build_blank_ground_truth(args.template_id, question_count)
    png_bytes, _ = SyntheticSheetGenerator.build(synthetic, gt, "clean")

    # 3) Calibrate -> v2 normalized TemplateProfile.
    try:
        profile = Calibrator.calibrate_from_synthetic(
            synthetic, template_id=args.template_id
        )
    except TemplateValidationError as exc:
        print("ERROR: calibration produced an invalid template:", file=sys.stderr)
        for err in exc.report.errors:
            print(f"  - {err.code.value}: {err.message}", file=sys.stderr)
        return 1

    # 4) Persist artifacts.
    json_path = out_dir / f"template-{args.template_id}.json"
    png_path = out_dir / f"blank-{args.template_id}.png"
    save_template_json(json_path, profile)
    png_path.write_bytes(png_bytes)

    print(f"template saved : {json_path}")
    print(f"blank card    : {png_path}")
    print(f"questions     : {question_count}")
    print(f"option cells  : {len(profile.get_all_option_cells())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
