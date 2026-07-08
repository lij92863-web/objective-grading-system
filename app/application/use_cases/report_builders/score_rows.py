"""Simple score rows builder — matches legacy ``simple_score_rows``."""

from collections import defaultdict


def _competition_ranks(results: list) -> list:
    sorted_results = sorted(enumerate(results), key=lambda item: (-item[1]["score"], item[0]))
    ranks = [0 for _ in results]
    prev = None; cur = 0
    for pos, (idx, r) in enumerate(sorted_results, start=1):
        if prev is None or r["score"] != prev: cur = pos
        ranks[idx] = cur; prev = r["score"]
    return ranks


def build_simple_score_rows(results: list) -> list:
    ranks = _competition_ranks(results)
    rows = []
    for idx, result in enumerate(results):
        details = result.get("details", [])
        by_status = defaultdict(list)
        for d in details:
            by_status[d.get("status", "")].append(str(d.get("number", d.get("question", ""))))
        pct = result.get("percent", 0)
        remarks = []
        if pct >= 90: remarks.append("优秀")
        elif pct < 60: remarks.append("未及格")
        if by_status.get("blank"): remarks.append("有空白")
        if by_status.get("invalid") or by_status.get("unrecognized"): remarks.append("有异常")
        rows.append(dict(
            rank=ranks[idx],
            student_id=result["student_id"],
            name=result.get("name", ""),
            score=result["score"],
            max_score=result.get("max_score", 0),
            percent=result.get("percent", 0),
            correct_count=result.get("correct_count", 0),
            wrong_or_partial_count=result.get("wrong_or_partial_count", 0),
            blank_count=result.get("blank_count", 0),
            invalid_count=result.get("invalid_count", 0),
            wrong_questions=";".join(by_status.get("wrong", []) + by_status.get("invalid", [])),
            blank_questions=";".join(by_status.get("blank", [])),
            remark="；".join(remarks) if remarks else "",
        ))
    return rows
