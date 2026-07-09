#!/usr/bin/env python3
"""R109: Teacher-facing summary synthetic CLI."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    result = {"exam_id": "exam-001", "batch_id": "batch-001",
              "total_students": 3, "processed_students": 3, "ready_students": 2,
              "needs_review_students": 1, "blocked_students": 0,
              "total_items": 45, "auto_accepted_items": 40, "needs_review_items": 3,
              "blocking_items": 2, "top_review_reasons": ["OMR/Qwen conflict", "blank low confidence"],
              "students_needing_attention": ["S003"], "questions_needing_attention": ["Q2", "Q5"]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
