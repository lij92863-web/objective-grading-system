"""Class report builder — matches legacy ``build_class_report``."""

import json
import statistics


def build_class_report(exam_meta: dict, questions: list, results: list, profiles: list) -> list:
    rows = []
    rows.append(dict(section="exam", metric="exam_name", value=exam_meta.get("exam_name", ""), extra=""))
    rows.append(dict(section="exam", metric="class_name", value=exam_meta.get("class_name", ""), extra=""))
    rows.append(dict(section="exam", metric="subject", value=exam_meta.get("subject", ""), extra=""))
    rows.append(dict(section="exam", metric="exam_date", value=exam_meta.get("exam_date", ""), extra=""))

    scores = [r["score"] for r in results]
    max_sc = sum(q.get("points", 0) for q in questions if q.get("status", "normal") not in ("cancelled", "manual_review"))
    rows.append(dict(section="score", metric="student_count", value=len(results), extra=""))
    rows.append(dict(section="score", metric="max_score", value=round(max_sc, 4), extra=""))
    if scores:
        rows.append(dict(section="score", metric="average", value=round(statistics.mean(scores), 2), extra=""))
        rows.append(dict(section="score", metric="median", value=round(statistics.median(scores), 2), extra=""))
        rows.append(dict(section="score", metric="highest", value=round(max(scores), 2), extra=""))
        rows.append(dict(section="score", metric="lowest", value=round(min(scores), 2), extra=""))
        pass_cnt = sum(1 for r in results if r.get("percent", 0) >= 60)
        exc_cnt = sum(1 for r in results if r.get("percent", 0) >= 90)
        low_cnt = sum(1 for r in results if r.get("percent", 0) < 60)
        total = len(results) or 1
        rows.append(dict(section="score", metric="pass_rate", value=round(pass_cnt / total * 100, 2), extra="percent >= 60"))
        rows.append(dict(section="score", metric="excellent_rate", value=round(exc_cnt / total * 100, 2), extra="percent >= 90"))
        rows.append(dict(section="score", metric="low_score_rate", value=round(low_cnt / total * 100, 2), extra="percent < 60"))
        bands = [("90%-100%", 90, 101), ("80%-89%", 80, 90), ("70%-79%", 70, 80),
                  ("60%-69%", 60, 70), ("below_60%", 0, 60)]
        for label, lo, hi in bands:
            cnt = sum(1 for r in results if lo <= r.get("percent", 0) < hi)
            pct_val = round(cnt / total * 100, 2)
            rows.append(dict(section="score_band", metric=label, value=cnt, extra=f"{pct_val}%"))

    # Knowledge section
    tag_scores = {}
    tag_counts = {}
    for p in profiles:
        tag = p.get("tag", "")
        tag_scores[tag] = tag_scores.get(tag, 0.0) + p.get("mastery", 0)
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    weak_students = {}
    for p in profiles:
        weak_val = p.get("weak")
        if weak_val == "yes" or weak_val is True:
            weak_students[p.get("tag", "")] = weak_students.get(p.get("tag", ""), 0) + 1
    for tag in sorted(tag_scores):
        avg = round(tag_scores[tag] / tag_counts[tag], 2) if tag_counts.get(tag) else 0
        wc = weak_students.get(tag, 0)
        rows.append(dict(section="knowledge", metric=tag, value=avg, extra=f"weak_students={wc}"))

    # Item section (per-question summary)
    for q in questions:
        qnum = q.get("question", 0)
        q_tags = q.get("tags", [])
        if isinstance(q_tags, str): q_tags = [t.strip() for t in q_tags.split(";") if t.strip()]
        details = [d for r in results for d in r.get("details", [])
                   if d.get("number", d.get("question")) == qnum]
        total = len(details) or 1
        correct = sum(1 for d in details if d.get("status") in ("correct", "bonus"))
        accuracy = round(correct / total * 100, 2)
        blank = sum(1 for d in details if d.get("status") == "blank")
        blank_rate = round(blank / total * 100, 2)
        wrong = sum(1 for d in details if d.get("status") in ("wrong", "invalid", "unrecognized"))
        wrong_rate = round(wrong / total * 100, 2)
        partial = sum(1 for d in details if d.get("status") == "partial")
        partial_rate = round(partial / total * 100, 2)
        from collections import Counter as _Counter
        distribution = _Counter(d.get("normalized_answer") or d.get("actual", "") or "(blank)" for d in details)
        dist_json = json.dumps(dict(distribution), ensure_ascii=False)
        extra = (
            f"tags={'/'.join(q_tags)};blank_rate={blank_rate}"
            f";wrong_rate={wrong_rate};partial_rate={partial_rate}"
            f";option_distribution={dist_json}"
        )
        rows.append(dict(section="item", metric=f"Q{qnum}", value=accuracy, extra=extra))
    return rows
