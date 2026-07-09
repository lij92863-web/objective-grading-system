"""Recognition evaluation metrics."""
from typing import Any, Dict, List
from .contracts import RecognitionRunResult


def evaluate_recognition_result(result: RecognitionRunResult,
                                 expected_answers: Dict[int, str]) -> Dict[str, Any]:
    drafts = result.drafts
    if not drafts: return {"error": "no_drafts"}
    decisions = drafts[0].decisions
    total = len(decisions)
    correct = sum(1 for d in decisions if str(d.question_number) in expected_answers and
                  d.value == expected_answers[str(d.question_number)])
    auto = sum(1 for d in decisions if d.status == "auto_accepted")
    false_auto = sum(1 for d in decisions if d.status == "auto_accepted" and
                     str(d.question_number) in expected_answers and
                     d.value != expected_answers[str(d.question_number)])
    review = sum(1 for d in decisions if d.needs_review)
    blocking = sum(1 for d in decisions if d.blocking)
    return {"total": total, "correct": correct, "accuracy": round(correct/total*100,2) if total else 0,
            "auto_accepted": auto, "false_auto_accept": false_auto,
            "review_rate": round(review/total*100,2) if total else 0,
            "blocking_rate": round(blocking/total*100,2) if total else 0,
            "needs_review_count": review}
