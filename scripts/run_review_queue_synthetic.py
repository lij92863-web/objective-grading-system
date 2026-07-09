#!/usr/bin/env python3
"""R86: Review queue synthetic CLI."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.recognition.contracts import RecognitionDecision
from app.recognition.review_queue_builder import build_review_queue, summary
from app.recognition.review_summary import build_review_summary


def main():
    decisions = [
        RecognitionDecision(question_number=1, value="A", status="auto_accepted", needs_review=False),
        RecognitionDecision(question_number=2, value="B", status="needs_review", needs_review=True, reason="omr_qwen_conflict"),
        RecognitionDecision(question_number=5, value="", status="blank", needs_review=True, reason="blank_low_confidence"),
        RecognitionDecision(question_number=10, value="E", status="invalid", blocking=True, needs_review=True, reason="invalid_option"),
    ]
    items = build_review_queue(decisions, student_ref="S001", draft_id="d1")
    queue_summary = summary(items)
    teacher_summary = build_review_summary(items)
    result = {"review_queue_summary": queue_summary, "teacher_facing": teacher_summary}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
