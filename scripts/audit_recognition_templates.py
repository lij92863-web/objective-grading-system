#!/usr/bin/env python3
"""R54: Audit all recognition templates."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.layout import load_answer_sheet_layout, validate_answer_sheet_layout

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "recognition" / "templates"


def main():
    results = {"total": 0, "valid": 0, "invalid": 0, "details": []}
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        results["total"] += 1
        try:
            layout = load_answer_sheet_layout(f)
            errors = validate_answer_sheet_layout(layout)
            valid = len(errors) == 0
            results["details"].append({"file": f.name, "valid": valid, "errors": errors,
                                        "questions": len(layout.question_rois)})
            if valid: results["valid"] += 1
            else: results["invalid"] += 1
        except Exception as e:
            results["details"].append({"file": f.name, "valid": False, "errors": [str(e)]})
            results["invalid"] += 1
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
