"""CLI to generate the committed synthetic answer-sheet corpus.

This script renders a small, representative set of synthetic sheets (PNGs) plus
their ground-truth JSON and a corpus manifest. The output lives under
``tests/student_recognition/fixtures/synthetic/`` so it can be committed (these
are synthetic images, not real student photos -- constitution §1 B5).

Pure standard library + ``argparse``; no new dependencies (constitution §1 B4).

Usage:
    python scripts/student_recognition/generate_synthetic_corpus.py \
        --out tests/student_recognition/fixtures/synthetic --count 16 --seed 12345
"""

import argparse
import json
import sys
from pathlib import Path

# Make the project root importable when run as a bare script.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.student_recognition.synthetic.corpus import (  # noqa: E402
    build_ground_truth,
    default_corpus_spec,
)
from app.student_recognition.synthetic.generator import (  # noqa: E402
    SyntheticSheetGenerator,
)
from app.student_recognition.synthetic.template_profile import (  # noqa: E402
    build_default_template,
)

DEFAULT_OUT = ROOT / "tests" / "student_recognition" / "fixtures" / "synthetic"
DEFAULT_COUNT = 16
DEFAULT_SEED = 12345


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the synthetic answer-sheet corpus.")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory (default: tests/student_recognition/fixtures/synthetic).",
    )
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="Number of sheets (default: 16).")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Base random seed (default: 12345).")
    args = parser.parse_args(argv)

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    template = build_default_template()
    _write_json(out_dir / "template_profile.json", template.to_dict())
    print(f"[corpus] wrote template_profile.json (template_id={template.template_id})")

    specs = default_corpus_spec(template, count=args.count, seed=args.seed)
    manifest = {
        "template_id": template.template_id,
        "schema_version": template.schema_version,
        "seed": args.seed,
        "count": len(specs),
        "sheets": [],
    }

    for spec in specs:
        gt = build_ground_truth(spec, template)
        png_bytes, _ = SyntheticSheetGenerator.build(template, gt, gt.perturbation)
        sheet_id = gt.sheet_id
        png_path = out_dir / f"{sheet_id}.png"
        gt_path = out_dir / f"{sheet_id}.gt.json"
        png_path.write_bytes(png_bytes)
        _write_json(gt_path, gt.to_dict())
        manifest["sheets"].append(
            {
                "sheet_id": sheet_id,
                "perturbation": gt.perturbation,
                "png": png_path.name,
                "gt": gt_path.name,
            }
        )
        print(f"[corpus] wrote {sheet_id}.png + {sheet_id}.gt.json (perturbation={gt.perturbation})")

    _write_json(out_dir / "corpus_manifest.json", manifest)
    print(f"[corpus] wrote corpus_manifest.json with {len(specs)} sheets -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
