"""Item analysis builder — matches legacy ``item_stats``."""

from collections import Counter


def build_item_analysis_rows(answer_key_questions: list, results: list) -> list:
    """Return item-analysis rows matching legacy ``item_stats`` output.

    *answer_key_questions*: list of dicts with question, tags, answer, points, source_id, status, difficulty.
    *results*: list of dicts with 'details' (list of dicts with number, status, actual, score, max_score).
    """
    rows = []
    for spec in answer_key_questions:
        qnum = spec["question"]
        details = [d for r in results for d in r.get("details", []) if d.get("number", d.get("question")) == qnum]
        total = len(details) or 1
        correct = sum(1 for d in details if d.get("status") in ("correct", "bonus"))
        partial = sum(1 for d in details if d.get("status") == "partial")
        blank = sum(1 for d in details if d.get("status") == "blank")
        invalid = sum(1 for d in details if d.get("status") == "invalid")
        wrong = sum(1 for d in details if d.get("status") in ("wrong", "invalid", "unrecognized"))
        distribution = Counter(d.get("normalized_answer") or d.get("actual", "") or "(blank)" for d in details)
        rows.append(dict(
            question=spec["question"],
            tags=";".join(spec.get("tags", []) if isinstance(spec.get("tags"), (list, tuple)) else [spec.get("tags", "")]),
            answer=spec.get("answer_text") or spec.get("answer", ""),
            accuracy=round(correct / total * 100, 2),
            blank_rate=round(blank / total * 100, 2),
            invalid_rate=round(invalid / total * 100, 2),
            wrong_rate=round(wrong / total * 100, 2),
            partial_rate=round(partial / total * 100, 2),
            mistake_count=wrong + partial,
            distribution=dict(distribution),
        ))
    return rows
