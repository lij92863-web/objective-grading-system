#!/usr/bin/env python3
"""R32: Template validator CLI."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.layout import load_answer_sheet_layout, validate_answer_sheet_layout


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--template", required=True)
    args = p.parse_args()
    try:
        layout = load_answer_sheet_layout(args.template)
        errors = validate_answer_sheet_layout(layout)
        warnings = [] if layout.question_rois else ["no_question_rois"]
        result = {"valid": len(errors) == 0, "errors": errors, "warnings": warnings,
                  "summary": {"question_count": len(layout.question_rois),
                              "layout_id": layout.layout_id, "page_count": layout.page_count}}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if errors else 0
    except Exception as e:
        print(json.dumps({"valid": False, "errors": [str(e)]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
