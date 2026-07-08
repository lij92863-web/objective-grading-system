"""Item analysis builder — matches legacy ``write_item_analysis`` rows."""

import json
from collections import Counter


def build_item_analysis_rows(answer_key_questions: list, results: list) -> list:
    """Return item-analysis rows matching legacy ``write_item_analysis`` output.

    *answer_key_questions*: list of dicts with question, question_id, question_status,
      difficulty, tags, answer, points.
    *results*: list of dicts with 'details' (list of dicts with number, status, actual).
    """
    rows = []
    for spec in answer_key_questions:
        qnum = spec["question"]
        details = [d for r in results for d in r.get("details", [])
                   if d.get("number", d.get("question")) == qnum]
        total = len(details) or 1
        correct = sum(1 for d in details if d.get("status") in ("correct", "bonus"))
        partial = sum(1 for d in details if d.get("status") == "partial")
        blank = sum(1 for d in details if d.get("status") == "blank")
        invalid = sum(1 for d in details if d.get("status") == "invalid")
        wrong = sum(1 for d in details if d.get("status") in ("wrong", "invalid", "unrecognized"))
        distribution = Counter(
            d.get("normalized_answer") or d.get("actual", "") or "(blank)"
            for d in details
        )
        tags = spec.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(";") if t.strip()]
        rows.append(dict(
            question=spec["question"],
            question_id=spec.get("source_id", spec.get("question_id", "")),
            question_status=spec.get("status", "normal"),
            difficulty=spec.get("difficulty", 0),
            tags=";".join(tags),
            answer=spec.get("answer_text") or spec.get("answer", ""),
            points=spec.get("points", 0),
            accuracy=round(correct / total * 100, 2),
            blank_rate=round(blank / total * 100, 2),
            wrong_rate=round(wrong / total * 100, 2),
            partial_rate=round(partial / total * 100, 2),
            invalid_rate=round(invalid / total * 100, 2),
            option_distribution=json.dumps(dict(distribution), ensure_ascii=False),
        ))
    return rows
